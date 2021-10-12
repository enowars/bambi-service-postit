from Crypto.PublicKey import RSA

def sign(m, d, n):
    return pow(m, d, n)

e = 3
key = RSA.generate(1024, e = e)

print(e)
print(key.n)

while True:
    msg = input()
    msg = int.from_bytes(msg.encode(), byteorder="big")
    print(sign(msg, key.d, key.n))
