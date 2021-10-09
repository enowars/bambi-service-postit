# bambi-service-forgetmenot
Service for BambiCTF #6

## Draft in German

RSA-signatures, checked with strcmp in C

* terminal-based "Post-Its"
* register with name and public key
* get all user names
* to add a note, sign the sha512-value with your private key
* requests notes for a user:
	* get the public key and a token to sign
	* if signature correct, get all messages from that user

Checker only uses keys with e = 3, then can forge signatures for short messages (but not 512 bits).
siganture = ceil((m + \x00 * foo) ^ (1/e))
When checking: signature^e = m + \x00 + ..., and strcmp accepts
