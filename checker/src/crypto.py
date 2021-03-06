#!/usr/bin/env python3

import random
from os import listdir
from typing import List, Tuple

from gmpy2 import iroot, mpz  # type: ignore

from util import bytes2int, int2bytes

keys: List["RSA"] = []


class RSA:
    def __init__(self, data: Tuple[int, int, int]):
        self.e = data[0]
        self.d = data[1]
        self.n = data[2]

    def encode(self) -> Tuple[str, str, str]:
        return (str(self.e), str(self.d), str(self.n))

    @classmethod
    def decode(cls, params: Tuple[str, str, str]) -> "RSA":
        return cls((int(params[0]), int(params[1]), int(params[2])))


def load_keys() -> None:
    for file in listdir("keys"):
        params = tuple(int(v) for v in open(f"keys/{file}").read().split())
        keys.append(RSA((params[0], params[1], params[2])))
    assert len(keys) > 0


def get_key() -> "RSA":
    assert len(keys) != 0
    return random.choice(keys)


def sign(m: bytes, rsa: "RSA") -> int:
    return int(pow(bytes2int(m), rsa.d, rsa.n))


def fake_sign(m: bytes, exp: int, mod: int) -> int:
    assert exp == 3
    padm = m + b"\x00" * (1 + 2 * 18)
    n = mpz(bytes2int(padm))
    sig, true_root = iroot(n, 3)
    if not true_root:
        sig += 1
    assert int2bytes(int(pow(sig, exp, mod))).startswith(m + b"\x00")
    return sig
