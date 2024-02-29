from copy import deepcopy
from argparse import ArgumentParser
from Crypto.Hash import MD5, SHA256, SHA512
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

class sLinDAP2P:

    min_rand = 1000000
    max_rand = 9999999
    bytes_len = 3

    def __init__(self, args: ArgumentParser, transformations: int = 100000):
        print(args)

        self.verbose = args.verbose
        self.keyring = sLinDAKeyring()

        self.__sha_iter = transformations
        self.__aes_key = self._get_aes_key(args.password)
        self.__aes_iv = self.__get_iv(args)

        #self.__test_aes()

    def encrypt(self, data: bytes) -> bytes:
        cipher = AES.new(self.__aes_key, AES.MODE_CBC, iv=self.__aes_iv)
        cipher_text = cipher.encrypt(pad(data, AES.block_size))
        return cipher_text

    def decrypt(self, ciper: bytes) -> bytes:
        decrypt_cipher = AES.new(self.__aes_key, AES.MODE_CBC, self.__aes_iv)
        data = decrypt_cipher.decrypt(ciper)
        unpadded = None
        try:
            unpadded = unpad(data, AES.block_size)
        except Exception as ex:
            print("Can not unpadding data, wrong key?")
        return unpadded

    #def encrypt_text(self, text: str) -> bytes:
    #    return self.encrypt(bytes(text, "utf8"))

    #def decrypt_text(self, data: bytes) -> str:
    #    return self.decrypt(data).decode('utf8')

    def _get_aes_key(self, passphrase: str):
        if self.verbose >= 2:
            print("Start SHA512 transformations iterations %d" % self.__sha_iter)
        hash = SHA512.new()
        hash.update(bytes(passphrase, encoding='utf8'))
        for i in range(0, self.__sha_iter):
            hash.update(hash.digest())
        aes_key = SHA256.new(hash.digest()).digest()

        if self.verbose >= 2:
            print("AES Key: %s" % aes_key)

        return aes_key

    def __get_iv(self, args: ArgumentParser):
        addresses: list = deepcopy(args.p)
        addresses.append(args.host)
        addresses.sort()
        iv = MD5.new(bytes(str(addresses), encoding='utf8')).digest()

        if self.verbose >= 2:
            print("Initialization vector: %s" % iv)

        return iv

    def __test_aes(self):
        cipher = self.encrypt_text("Test")
        text = self.decrypt_text(cipher)

        if self.verbose >= 2:
            print(cipher)
            print(text)

class sLinDAKeyring:

    _peers: dict = {"R": {}, "S": {}}

    def __init__(self):
        pass

    def get_peers(self):
        return self._peers

    def add_peer(self, identifier, aes_key: bytes, receiver: bool = True):
        self._peers["R" if receiver else "S"].update({identifier: aes_key})


