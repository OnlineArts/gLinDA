from copy import deepcopy
from argparse import ArgumentParser
from Crypto.Hash import MD5, SHA256, SHA512
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad


class sLinDAP2P:

    sha_iter: int = 100000
    min_rand: int = 1000000
    max_rand: int = 9999999
    bytes_len: int = 3
    waiting_time: int = 2
    chunk_size: int = 1024

    def __init__(self, args: ArgumentParser, keyring: object = None):
        self.verbose: int = args.verbose
        self.host: str = args.host
        self.peers: list = args.p
        self.test: str = args.test

        if keyring is not None:
            self.keyring = keyring
            print(self.keyring)
        else:
            self.keyring = sLinDAKeyring()
            self.__aes_key = self._get_aes_key(args.password)
        self.__aes_iv = self.__get_iv(args)

    def encrypt(self, data: bytes, aes_key: bytes = None) -> bytes:
        if aes_key is None:
            key = self.__aes_key
        else:
            key = aes_key
        cipher = AES.new(key, AES.MODE_CBC, iv=self.__aes_iv)
        cipher_text = cipher.encrypt(pad(data, AES.block_size))
        return cipher_text

    def decrypt(self, ciper: bytes, aes_key: bytes = None) -> bytes:
        if aes_key is None:
            key = self.__aes_key
        else:
            key = aes_key
        decrypt_cipher = AES.new(key, AES.MODE_CBC, self.__aes_iv)
        data = decrypt_cipher.decrypt(ciper)
        unpadded = None
        try:
            unpadded = unpad(data, AES.block_size)
        except Exception as ex:
            print("Can not unpadding data, wrong key?")
        return unpadded

    def _get_aes_key(self, password: str, skip_iterations: bool = False):
        hash = SHA512.new()
        hash.update(bytes(password, encoding='utf8'))
        if not skip_iterations:
            if self.verbose >= 2:
                print("Start SHA512 transformations iterations %d" % self.sha_iter)
            for i in range(0, self.sha_iter):
                hash.update(hash.digest())
        aes_key = SHA256.new(hash.digest()).digest()

        if self.verbose >= 2:
            print("New AES key: %s" % aes_key)

        return aes_key

    def __get_iv(self, args: ArgumentParser):
        """
        Creates an initialization vector for the AES CBC mode.
        The vector have to be the same for each peer, therefore it
        will be generated from the list of all involved host.
        :param args: all arguments
        :return:
        """
        addresses: list = deepcopy(args.p)
        addresses.append(args.host)
        addresses.sort()

        # put the list into an MD5 hash to achieve the right byte size.
        iv = MD5.new(bytes(str(addresses), encoding='utf8')).digest()

        if self.verbose >= 2:
            print("Initialization vector: %s" % iv)

        return iv


class sLinDAKeyring:

    _peers: dict = {"R": {}, "S": {}}

    def __init__(self):
        pass

    def add_peer(self, identifier, aes_key: bytes, receiver: bool = True):
        self._peers["R" if receiver else "S"].update({identifier: aes_key})

    def get_peers(self):
        return self._peers

    def __len__(self):
        return len(self._peers["R"].keys()) + len(self._peers["S"].keys())

    def for_reception(self, id: int):
        return self._peers["R"][id]

    def for_submission(self, host: str) -> list:
        return self._peers["S"][host]
