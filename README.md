# POSTIT

Service for BambiCTF #6

## Idea

RSA signatures, checked with strcmp in C

* terminal-based "Post-Its"
* register with name and public key
* get all user names
* to add a note, sign the challenge with your private key
* request posts for a user:
	* get the public key and a token to sign
	* if signature correct, get all messages from that user

Checker only uses keys with e = 3, then can forge signatures for
short messages (but not 512 bits).

signature = ceil((m + \x00 * foo) ^ (1/e))
When checking: signature^e = m + \x00 + ..., and strcmp accepts

## Exploits

Check out the exploit implementation in `checker/src/checker.py`.

