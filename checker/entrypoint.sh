#!/bin/bash

set -e

env

python3 -c '
from Crypto.PublicKey import RSA
from sys import argv
from os import environ, listdir

# use less keys for ci runner
count = 30 if environ.get("CI_RUNNER") == "1" else 500

files = listdir("keys")
for i in range(len(files), count):
    with open(f"keys/{i}.rsa", "w+") as f:
        print(f"Generating key {i+1}/{count}", flush=True)
        rsa = RSA.generate(1024, e=3)
        f.write(f"{rsa.e} {rsa.d} {rsa.n}")
print(f"{count} keys available.", flush=True)
'

/home/checker/.local/bin/gunicorn -c gunicorn.conf.py checker:app
