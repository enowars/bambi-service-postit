#!/usr/bin/env python3

import math
import random
import string
import time
from logging import LoggerAdapter
from typing import Any


def bytes2int(s: bytes) -> int:
    return int.from_bytes(s, byteorder="big")


def int2bytes(i: int) -> bytes:
    blen = math.ceil(math.log2(i) / 8)
    return int.to_bytes(i, byteorder="big", length=blen)


def gen_username() -> bytes:
    # TODO: fluff
    chars = [random.choice(string.ascii_letters) for i in range(32)]
    return "".join(chars).encode()


def gen_noise() -> bytes:
    # TODO: fluff, rick-roll b64 image, ...
    chars = [random.choice(string.ascii_letters) for i in range(32)]
    return "".join(chars).encode()


async def timed(promise: Any, logger: LoggerAdapter, ctx: str) -> Any:
    logger.debug("START: {}".format(ctx))
    start = time.time()
    result = await promise
    end = time.time()
    logger.debug("DONE:  {} (took {:.3f} seconds)".format(ctx, end - start))
    return result
