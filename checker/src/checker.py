#!/usr/bin/env python3

import re
from asyncio import StreamReader, StreamWriter
from asyncio.exceptions import TimeoutError
from logging import LoggerAdapter
from typing import Any, List, Optional, Tuple, cast

from enochecker3 import (
    AsyncSocket,
    ChainDB,
    DependencyInjector,
    Enochecker,
    ExploitCheckerTaskMessage,
    FlagSearcher,
    GetflagCheckerTaskMessage,
    GetnoiseCheckerTaskMessage,
    InternalErrorException,
    MumbleException,
    PutflagCheckerTaskMessage,
    PutnoiseCheckerTaskMessage,
)

from crypto import RSA, fake_sign, gen_keys, get_key, sign
from util import gen_noise, gen_username, timed

OK = 0
FAIL = 1

prompt = b"\r$ "


class Session:
    def __init__(self, socket: AsyncSocket, logger: LoggerAdapter) -> None:
        socket_tuple = cast(tuple[StreamReader, StreamWriter], socket)
        self.reader = socket_tuple[0]
        self.writer = socket_tuple[1]
        self.logger = logger
        # TODO: set prefix per session if objects not shared
        # TODO: add set_task for task information in logging output
        self.closed = False

    async def __aenter__(self) -> "Session":
        self.logger.debug("Preparing session")
        await self.prepare()
        return self

    async def __aexit__(self, *args: list[Any], **kwargs: dict[str, Any]) -> None:
        self.logger.debug("Closing session")
        await self.close()

    async def readuntil(
        self, target: bytes, include: bool = True, ctx: Optional[str] = None
    ) -> bytes:
        try:
            ctxstr = f"readuntil {target!r}" if ctx is None else ctx
            data = await timed(self.reader.readuntil(target), self.logger, ctx=ctxstr)
            msg = f"read:  {data[:100]!r}{'..' if len(data) > 100 else ''}"
            self.logger.debug(msg)
            if not include:
                data = data[: -len(target)]
            return data
        except TimeoutError:
            self.logger.critical(f"Service timed out while waiting for {target!r}")
            raise MumbleException("Service took too long to respond")

    async def readline(self, ctx: Optional[str] = None) -> bytes:
        return await self.readuntil(b"\n", ctx=ctx)

    async def read(self, n: int, ctx: Optional[str] = None) -> bytes:
        try:
            ctxstr = f"reading {n} bytes" if ctx is None else ctx
            data = await timed(self.reader.readexactly(n), self.logger, ctx=ctxstr)
            msg = f"read:  {data[:60]!r}{'..' if len(data) > 60 else ''}"
            self.logger.debug(msg)
            return data
        except TimeoutError:
            self.logger.critical(f"Service timed out while reading {n} bytes")
            raise MumbleException("Service took too long to respond")

    async def drain(self) -> None:
        await self.writer.drain()

    def write(self, data: bytes) -> None:
        msg = f"write: {data[:60]!r}{'..' if len(data) > 60 else ''}"
        self.logger.debug(msg)
        self.writer.write(data)

    async def prepare(self) -> None:
        await self.readuntil(prompt)

    async def exit(self) -> None:
        if self.closed:
            return
        self.write(b"exit\n")
        await self.drain()
        await self.readuntil(b"bye!")
        await self.close()

    async def close(self) -> None:
        if self.closed:
            return
        self.closed = True
        self.writer.close()
        await self.writer.wait_closed()


class _Enochecker(Enochecker):
    async def _init(self) -> None:
        count = 30
        gen_keys(count, lambda x: self._logger.debug(f"Generated RSA key {x}/{count}"))
        await super()._init()


checker = _Enochecker("postit", 9337)
app = lambda: checker.app


@checker.register_dependency
def _get_session(socket: AsyncSocket, logger: LoggerAdapter) -> Session:
    return Session(socket, logger)


async def getdb(db: ChainDB, key: str) -> tuple[Any, ...]:
    try:
        return await db.get(key)
    except KeyError:
        raise MumbleException(
            "Could not retrieve necessary info for service interaction"
        )


async def get_users(
    session: Session, expect: int = OK
) -> Tuple[int, Optional[List[bytes]]]:
    session.write(b"users\n")
    await session.drain()
    resp = await session.readuntil(prompt, include=False)
    try:
        return OK, [
            line.split(b"- ", 1)[1] for line in resp.split(b"\n") if line != b""
        ]
    except IndexError:
        if expect == FAIL:
            return FAIL, None
        session.logger.critical(f"Unexpected response when retrieving users:\n{resp!r}")
        raise MumbleException("Failed to retrieve user list")


async def register(
    session: Session, username: bytes, rsa: "RSA", expect: int = OK
) -> int:
    session.write(b"register %b\n%i\n%i\n" % (username, rsa.e, rsa.n))
    await session.drain()
    resp = await session.readuntil(prompt, include=False)
    if not resp.endswith(b"Enter RSA modulus: "):
        if expect == FAIL:
            return FAIL
        session.logger.critical(
            f"Unexpected response during registration of user {username!r}:\n{resp!r}"
        )
        raise MumbleException("Registration not working properly")

    _, users = await get_users(session)
    assert users is not None
    if username not in users:
        if expect == FAIL:
            return FAIL
        session.logger.critical(
            f"Registered user {username!r} missing from user list\n"
        )
        raise MumbleException("Registration not working properly")

    return OK


async def login(session: Session, username: bytes, rsa: "RSA", expect: int = OK) -> int:
    session.write(b"login %b\n" % username)
    await session.drain()

    resp = await session.readuntil(b"Signature: ")
    match = re.search(b"Sign this message: (.+)\n", resp)
    assert match is not None
    challenge = match.group(1)

    try:
        signature = sign(challenge, rsa)
    except ValueError as e:
        session.logger.critical(
            f"Failed to generate signature: {e}\n\
                Public exponent: {rsa.e!r}\n\
                Private exponent: {rsa.d!r}\n\
                Modulus: {rsa.n!r}"
        )
        raise InternalErrorException("Failed to sign message")

    session.write(b"%i\n" % signature)
    await session.drain()

    resp = await session.readuntil(prompt, include=False)
    if resp != b"":
        if expect == FAIL:
            return FAIL
        session.logger.critical(
            f"Unexpected response during registration of user {username!r}:\n\
                Public exponent: {rsa.e!r}\n\
                Private exponent: {rsa.d!r}\n\
                Modulus: {rsa.n!r}\n\
                Challenge: {challenge!r}\n\
                Signature: {signature!r}\n\
                Response: {resp!r}"
        )
        raise MumbleException("Authentication not working properly")

    return OK


async def userinfo(
    session: Session, username: bytes, expect: int = OK
) -> Tuple[int, Optional[Tuple[int, int]]]:
    session.write(b"info %b\n" % username)
    await session.drain()
    resp = await session.readuntil(prompt, include=False)
    match = re.search(b"Username: (.+)\nRSA Exponent: (.+)\nRSA Modulus: (.+)\n", resp)
    if match is None:
        if expect == FAIL:
            return FAIL, None
        session.logger.critical(
            f"Unable to retrieve info for user {username!r}\n\
                Received instead:\n{resp!r}"
        )
        raise MumbleException("User info not returned properly")

    return OK, (int(match.group(2)), int(match.group(3)))


async def get_posts(
    session: Session, expect: int = OK
) -> Tuple[int, Optional[List[bytes]]]:
    session.write(b"posts\n")
    await session.drain()
    resp = await session.readuntil(prompt, include=False)

    try:
        return OK, [
            line.split(b"- ", 1)[1] for line in resp.split(b"\n") if line != b""
        ]
    except IndexError:
        if expect == FAIL:
            return FAIL, None
        session.logger.critical(
            f"Unexpected response while retrieving posts:\n{resp!r}"
        )
        raise MumbleException("Post listing not working properly")


async def add_post(session: Session, msg: bytes, expect: int = OK) -> int:
    session.write(b"post %b\n" % msg)
    await session.drain()
    resp = await session.readuntil(prompt, include=False)
    if resp != b"":
        if expect == FAIL:
            return FAIL
        session.logger.critical(f"Unexpected response for post creation:\n{resp!r}")
        raise MumbleException("Post creation not working properly")

    return OK


@checker.putflag(0)
async def putflag(task: PutflagCheckerTaskMessage, di: DependencyInjector) -> str:
    db = await di.get(ChainDB)

    rsa = get_key()
    username = gen_username()

    session = await di.get(Session)
    await register(session, username, rsa)
    await login(session, username, rsa)
    await add_post(session, task.flag.encode())
    await session.exit()

    await db.set("info", (username, rsa.encode()))
    return "User '{}' just posted a secret".format(username.decode())


@checker.getflag(0)
async def getflag(task: GetflagCheckerTaskMessage, di: DependencyInjector) -> None:
    db = await di.get(ChainDB)
    username, rsa_params = await getdb(db, "info")
    rsa = RSA.decode(rsa_params)

    session = await di.get(Session)
    await login(session, username, rsa)
    _, posts = await get_posts(session)
    await session.exit()

    assert posts is not None
    if task.flag.encode() not in posts:
        session.logger.critical(f"Flag is missing from posts:\n{posts!r}")
        raise MumbleException("Failed to retrieve flag")


@checker.putnoise(0)
async def putnoise(task: PutnoiseCheckerTaskMessage, di: DependencyInjector) -> None:
    db = await di.get(ChainDB)

    rsa = get_key()
    username = gen_username()
    noise = gen_noise()

    session = await di.get(Session)
    await register(session, username, rsa)
    await login(session, username, rsa)
    await add_post(session, noise)
    await session.exit()

    await db.set("info", (username, rsa.encode(), noise))


@checker.getnoise(0)
async def getnoise(task: GetnoiseCheckerTaskMessage, di: DependencyInjector) -> None:
    db = await di.get(ChainDB)
    username, rsa_params, noise = await getdb(db, "info")
    rsa = RSA.decode(rsa_params)

    session = await di.get(Session)
    await login(session, username, rsa)
    _, posts = await get_posts(session)
    await session.exit()

    assert posts is not None
    if noise not in posts:
        session.logger.critical("Noise is missing from posts")
        raise MumbleException("Failed to retrieve noise")


@checker.exploit(0)
async def exploit(task: ExploitCheckerTaskMessage, di: DependencyInjector) -> None:
    assert task.attack_info is not None
    victim = task.attack_info[len("User '") : -len("' just posted a secret")].encode()
    searcher = await di.get(FlagSearcher)

    session = await di.get(Session)
    _, res = await userinfo(session, victim)
    assert res is not None
    exp, mod = res

    session.write(b"login %b\n" % victim)
    await session.drain()
    resp = await session.readuntil(b"Signature: ")

    match = re.search(b"Sign this message: (.+)\n", resp)
    assert match is not None
    challenge = match.group(1)

    try:
        signature = fake_sign(challenge, exp, mod)
    except (ValueError, AssertionError) as e:
        session.logger.critical(
            f"Failed to sign message: {e}\n\
                Public exponent: {exp!r}\n\
                Modulus: {mod!r}"
        )
        raise InternalErrorException("Failed generate fake signature")
    session.write(b"%i\n" % signature)
    await session.drain()

    resp = await session.readuntil(prompt, include=False)
    if resp != b"":
        raise MumbleException("Fake signature was rejected by service")

    _, posts = await get_posts(session)
    assert posts is not None
    if flag := searcher.search_flag(b"\n".join(posts)):
        return flag

    raise MumbleException("Exploit failed to find flag in posts")


if __name__ == "__main__":
    checker.run(port=9338)
