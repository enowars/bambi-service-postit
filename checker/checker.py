
#!/usr/bin/env python3
from enochecker import *

import binascii
from binascii import unhexlify, hexlify

from Crypto.PublicKey import RSA
from Crypto.Util.number import long_to_bytes, bytes_to_long
from hashlib import sha512
import random
import json

from crypto import decrypt, encrypt, sign, verify

private_key = RSA.importKey(open('checker.privkey','r').read())

class ForgetMeNotChecker(BaseChecker):
	"""
	Change the methods given here, then simply create the class and .run() it.
	Magic.
	A few convenient methods and helpers are provided in the BaseChecker.
	ensure_bytes ans ensure_unicode to make sure strings are always equal.
	As well as methods:
	self.connect() connects to the remote server.
	self.get and self.post request from http.
	self.team_db is a dict that stores its contents to filesystem. (call .persist() to make sure)
	self.readline_expect(): fails if it's not read correctly
	To read the whole docu and find more goodies, run python -m pydoc enochecker
	(Or read the source, Luke)
	"""

	flag_count = 1
	noise_count = 0
	havoc_count = 1
	service_name = "forgetmenot"
	port = 9122  # The port will automatically be picked up as default by self.connect and self.http.

	def flag_key(self):
		return f"flag_{self.flag_round}:{self.flag_idx}"

	def new_name(self):
		return "GoldFishBrain" + str(random.randint(1,1<<32))

	def putflag(self):  # type: () -> None
		"""
			This method stores a flag in the service.
			In case multiple flags are provided, self.flag_idx gives the appropriate index.
			The flag itself can be retrieved from self.flag.
			On error, raise an Eno Exception.
			:raises EnoException on error
			:return this function can return a result if it wants
					if nothing is returned, the service status is considered okay.
					the preferred way to report errors in the service is by raising an appropriate enoexception
		"""
		try:
			if self.flag_idx == 0:
				self.register_user()

				input_data = {'cmd' : 'post', 'name' : self.name, 'time' : int(time.time()) + random.randint(600, 660), 'note' : self.flag}
				msg = json.dumps(input_data)
				signature = sign(msg)

				conn = self.connect()
				expect_command_prompt(conn)
				conn.write(('%s:%s\n' % (msg, signature)).encode('utf-8'))

				self.debug(f"Sent msg to client: {input_data}")

				#expect service to return "sha512(flag):[index in my post-its]"
				try:
					ret = expect_command_prompt(conn).decode().strip().split(":")
					ret_hash = ret[0]
					ret_id = ret[1]
				except IndexError:
					conn.close()
					raise BrokenServiceException("Failed to parse hash")

				conn.close()

				self.debug(f"FLAG-hash: {sha512(self.flag.encode()).hexdigest().encode()}, returned {ret_hash.strip().encode()}")
				if sha512(self.flag.encode()).hexdigest() != ret_hash.strip():
					raise BrokenServiceException('Returned wrong hash')

				self.team_db[self.flag_key()] = ret_id

		except EOFError:
			raise OfflineException("Encountered unexpected EOF")
		except UnicodeError:
			self.debug("UTF8 Decoding-Error")
			raise BrokenServiceException("Fucked UTF8")

	def register_user(self):
		"""Register a new user in the service.
		Creates a new username and an RSA-key, to be used in the future.
		"""
		self.name = self.new_name()
		self.key = RSA.generate(1024, e = 3)
		self.team_db['name'] = self.name
		self.team_db['key'] = self.key.export_key()

		conn = self.connect()
		expect_command_prompt(conn)
		input_command = "register_user:%s:%d:%d" % (self.name, self.key.n, self.key.e)
		conn.write(input_data.encode('utf-8') + b"\n")
		conn.close()
	
	def getflag(self):  # type: () -> None
		"""
		This method retrieves a flag from the service.
		Use self.flag to get the flag that needs to be recovered and self.round to get the round the flag was placed in.
		On error, raise an EnoException.
		:raises EnoException on error
		:return this function can return a result if it wants
				if nothing is returned, the service status is considered okay.
				the preferred way to report errors in the service is by raising an appropriate enoexception
		"""
		try:
			if self.flag_idx == 0:
				#get old data
				try:
					flag_id = self.team_db[self.flag_key()]
				except IndexError:
					raise BrokenServiceException("Checked flag was not successfully deployed")
				try:
					self.name = self.team_db['name']
					self.key = self.team_db['key']
				except IndexError:
					raise BrokenServiceException("Cannot find user")

				conn = self.connect()
				expect_command_prompt(conn)
				input_data = {'cmd' : 'get', 'name' : self.name}
				msg = json.dumps(input_data)
				conn.write(msg.encode() + b'\n')

				pubkey = RSA.import_key(expect_command_prompt(conn).decode())
				challenge = expect_command_prompt(conn).decode()

				if pubkey.n != self.key.n or pubkey.e != self.key.e:
					raise BrokenServiceException("Wrong public key")

				#if this is bottleneck, change to fast signing, factor ~4
				signature = pow(int(challenge,16), self.key.d, self.key.n)

				conn.write(hexlify(long_to_bytes(signature)) + b'\n')
				notes = expect_command_prompt(conn).decode()

				if self.flag not in notes:
					#error might be because of updated public key, so renew it
					raise BrokenServiceException("Could not retrieve correct flag")

		except EOFError:
			raise OfflineException("Encountered unexpected EOF")
		except UnicodeError:
			self.debug("UTF8 Decoding-Error")
			raise BrokenServiceException("Fucked UTF8")

	def noise_key(self):
		return f"noise_{self.flag_round}:{self.flag_idx}"

	def putnoise(self):  # type: () -> None
		"""
		This method stores noise in the service. The noise should later be recoverable.
		The difference between noise and flag is, that noise does not have to remain secret for other teams.
		This method can be called many times per round. Check how often using self.flag_idx.
		On error, raise an EnoException.
		:raises EnoException on error
		:return this function can return a result if it wants
				if nothing is returned, the service status is considered okay.
				the preferred way to report errors in the service is by raising an appropriate enoexception
		"""
		try:
			if self.flag_idx == 0:
				joke = random.choice(open('jokes','r').read().split('\n\n'))
				joke_hex = hexlify(joke.encode()).decode()

				content = 'joke %s %d' % (joke_hex, self.flag_round)
				signature = sign(content, private_key)

				input_data = ('receive %s %s' % (content, signature)).encode()

				conn = self.connect()
				expect_command_prompt(conn)
				conn.write(input_data + b"\n")

				try:
					ret = expect_command_prompt(conn).decode().strip().split(":")
					self.debug(f"Service returned: \"{ret}\"")
					ret_hash = ret[0]
					joke_id = ret[1]
				except IndexError:
					conn.close()
					raise BrokenServiceException("Failed to parse hash")

				conn.close()
				self.debug(f"joke-hash: {sha256(joke.encode()).hexdigest().encode()}, returned {ret_hash.strip().encode()}")

				if sha256(joke.encode()).hexdigest() != ret_hash.strip():
					raise BrokenServiceException('Returned wrong hash')

				self.team_db[self.noise_key() + "joke"] = joke
				self.team_db[self.noise_key() + "joke_id"] = joke_id

		except EOFError:
			raise OfflineException("Encountered unexpected EOF")
		except UnicodeError:
			self.debug("UTF8 Decoding-Error")
			raise BrokenServiceException("Fucked UTF8")

	def getnoise(self):  # type: () -> None
		"""
		This method retrieves noise in the service.
		The noise to be retrieved is inside self.flag
		The difference between noise and flag is, that noise does not have to remain secret for other teams.
		This method can be called many times per round. Check how often using flag_idx.
		On error, raise an EnoException.
		:raises EnoException on error
		:return this function can return a result if it wants
				if nothing is returned, the service status is considered okay.
				the preferred way to report errors in the service is by raising an appropriate enoexception
		"""
		try:
			if self.flag_idx == 0:
				conn = self.connect()
				expect_command_prompt(conn)
				joke_id = self.team_db[self.noise_key() + "joke_id"]
				conn.write(f"send {joke_id}\n".encode() )
				joke_hex = expect_command_prompt(conn).decode().strip()
				self.debug(f"joke recieved: {joke_hex}, len {len(joke_hex)}")
				try:
					joke = unhexlify(joke_hex).decode()
				except binascii.Error:
					self.debug("failed to decode joke-hex")
					raise BrokenServiceException("Retrieved invalid joke")

				joke_orig = self.team_db[self.noise_key() + "joke"]
				self.debug(f"{joke_orig}, {joke}")
				if joke != joke_orig:
					raise BrokenServiceException("I didn't get the joke.")

		except EOFError:
			raise OfflineException("Encountered unexpected EOF")
		except UnicodeError:
			self.debug("UTF8 Decoding-Error")
			raise BrokenServiceException("Fucked UTF8")
		except KeyError:
			raise BrokenServiceException("Noise not found!")

	def havoc(self):  # type: () -> None
		"""
		This method unleashes havoc on the app -> Do whatever you must to prove the service still works. Or not.
		On error, raise an EnoException.
		:raises EnoException on Error
		:return This function can return a result if it wants
				If nothing is returned, the service status is considered okay.
				The preferred way to report Errors in the service is by raising an appropriate EnoException
		"""
		try:
			if self.flag_idx == 0:
				#get all users
				pass

		except EOFError:
			raise OfflineException("Encountered unexpected EOF")
		except UnicodeError:
			self.debug("UTF8 Decoding-Error")
			raise BrokenServiceException("Fucked UTF8")

	def exploit(self):
		"""
		This method was added for CI purposes for exploits to be tested.
		Will (hopefully) not be called during actual CTF.
		:raises EnoException on Error
		:return This function can return a result if it wants
				If nothing is returned, the service status is considered okay.
				The preferred way to report Errors in the service is by raising an appropriate EnoException
		"""
		pass

def expect_command_prompt(conn):
	return conn.readline_expect(b'command: ',b'command: ').split(b'command: ')[0] # need colon and space in split?

app = ForgetMeNotChecker.service  # This can be used for uswgi.
if __name__ == "__main__":
	run(ForbetMeNotChecker)
	# Example params could be: [StoreFlag localhost ENOFLAG 1 ENOFLAG 50 1]
	# exit(ExampleChecker(port=1337).run())