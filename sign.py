from Crypto.PublicKey import RSA

def sign(m, key):
    return pow(m, key.d, key.n)

e = 3
key = RSA.generate(1024, e = e)

print("Exponent:", e)
print("Modulus:", key.n)

while True:
    msg = input("Challenge: ")
    val = int.from_bytes(msg.encode(), byteorder="big")
    print("Signature:", sign(val, key))
