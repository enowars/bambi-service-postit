#!/usr/bin/env python3

import math
import secrets
import string
import time
from base64 import b64encode
from logging import LoggerAdapter
from os import path
from typing import Any

leetconv = {
    "O": "0",
    "l": "1",
    "I": "1",
    "Z": "2",
    "E": "3",
    "A": "4",
    "S": "5",
    "G": "6",
    "T": "7",
}

srcdir = path.dirname(path.abspath(__file__))
wordlist = open(f"{srcdir}/media/wordlist").read().replace(" ", "").split("\n")
names = [line for line in wordlist if line != ""]
rickroll = open(f"{srcdir}/media/rickroll.b64").read().replace("\n", "")
messages = [
    "Remember: invite Paul to lan party",
    "Shopping list: tomatoes and potatoes",
    "This is not the flag hehe",
    "🤓🤓🤓 Try Harder 🤓🤓🤓",
    "Crypto makes me go 🥴🤢🤮",
    "RSA, more like (R)eal (S)Bad (A)Crypto",
    "🤡 The flag is in another castle! 🤡",
    "🧠 solving crypto challenges with a calculator 🧠",
]
gplmsg = "You should have received a copy of the GNU \
General Public License along with this file; if not, \
write to the Free Software Foundation, Inc., 51 Franklin St, \
Fifth Floor, Boston, MA 02110-1301 USA"


def randint(low: int, high: int) -> int:
    return low + secrets.randbelow(high - low + 1)


def randbool() -> bool:
    return randint(0, 1) == 1


def randstr(n: int) -> str:
    alphabet = string.ascii_letters + string.digits
    chars = [secrets.choice(alphabet) for i in range(n)]
    return "".join(chars)


def bytes2int(s: bytes) -> int:
    return int.from_bytes(s, byteorder="big")


def int2bytes(i: int) -> bytes:
    assert i >= 0
    blen = 1 if i == 0 else math.ceil(math.log2(i) / 8)
    return int.to_bytes(i, byteorder="big", length=blen)


def spongebobcase(name: str) -> str:
    return "".join([(c.upper() if randbool() else c) for c in name])


def leetify(name: str) -> str:
    if randbool():
        name = spongebobcase(name)
    return "".join([(leetconv[c] if c in leetconv else c) for c in name])


def gen_username() -> bytes:
    msg = ""
    while len(msg) < randint(10, 30):
        part = secrets.choice(names)
        if randbool():
            part = leetify(part)
        msg += part
    username = msg + randstr(30)
    return username.encode()


def gen_noise() -> bytes:
    selection = randint(0, len(messages) + 2)
    if selection == 0:
        msg = randstr(randint(30, 60))
    elif selection == 1:
        msg = rickroll
    elif selection == 2:
        msg = gplmsg
    else:
        msg = secrets.choice(messages)
        if randbool():
            msg = b64encode(msg.encode()).decode()
    return msg.encode()


async def timed(promise: Any, logger: LoggerAdapter, ctx: str) -> Any:
    logger.debug("START: {}".format(ctx))
    start = time.time()
    result = await promise
    end = time.time()
    logger.debug("DONE:  {} (took {:.3f} seconds)".format(ctx, end - start))
    return result
