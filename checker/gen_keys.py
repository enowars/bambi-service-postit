from Crypto.PublicKey import RSA
from sys import argv
from os import listdir

count = int(argv[1])
files = listdir("keys")
for i in range(len(files), count):
    with open(f"keys/{i}.rsa", "w+") as f:
        print(f"\rGenerating key {i+1}/{count}", end="")
        rsa = RSA.generate(1024, e=3)
        f.write(f"{rsa.e} {rsa.d} {rsa.n}")
print()
