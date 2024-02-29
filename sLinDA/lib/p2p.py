from argparse import ArgumentParser
from Crypto.Hash import MD5, SHA256, SHA512
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad


class sLinDAP2P:

    def __init__(self, args: ArgumentParser, transformations: int = 100000):
        self.verbose = args.verbose

        self.__sha_iter = transformations
        self.__aes_key = self.__get_aes_key(args)
        self.__aes_iv = self.__get_iv(args)

        self.__test_aes()

    def _encrypt(self, data: bytes) -> bytes:
        cipher = AES.new(self.__aes_key, AES.MODE_CBC, iv=self.__aes_iv)
        cipher_text = cipher.encrypt(pad(data, AES.block_size))
        return cipher_text

    def _decrypt(self, ciper: bytes) -> bytes:
        decrypt_cipher = AES.new(self.__aes_key, AES.MODE_CBC, self.__aes_iv)
        data = decrypt_cipher.decrypt(ciper)
        return unpad(data, AES.block_size)

    def _encrypt_text(self, text: str) -> bytes:
        return self._encrypt(bytes(text, "utf8"))

    def _decrypt_text(self, data: bytes) -> str:
        return self._decrypt(data).decode('utf8')

    def __get_aes_key(self, args: ArgumentParser):
        if self.verbose >= 2:
            print("Start SHA512 transformations iterations %d" % self.__sha_iter)
        hash = SHA512.new()
        hash.update(bytes(args.password, encoding='utf8'))
        for i in range(0, self.__sha_iter):
            hash.update(hash.digest())
        aes_key = SHA256.new(hash.digest()).digest()

        if self.verbose >= 2:
            print("AES Key: %s" % aes_key)

        return aes_key

    def __get_iv(self, args: ArgumentParser):
        addresses: list = args.p
        addresses.append(args.host)
        addresses.sort()
        iv = MD5.new(bytes(str(addresses), encoding='utf8')).digest()

        if self.verbose >= 2:
            print("Initialization vector: %s" % iv)

        return iv

    def __test_aes(self):
        cipher = self._encrypt_text("Test")
        text = self._decrypt_text(cipher)

        if self.verbose >= 2:
            print(cipher)
            print(text)