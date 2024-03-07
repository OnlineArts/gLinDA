from copy import deepcopy
from Crypto.Hash import MD5, SHA256, SHA512
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad


class sLinDAP2P:

    sha_iter: int = 100000
    min_rand: int = 1000000
    max_rand: int = 9999999
    bytes_len: int = 3
    waiting_time: int = 2
    chunk_size: int = 1024000

    def __init__(self, config: dict, keyring: object = None):
        self.config: dict = config["P2P"]
        self.verbose: int = self.config["verbose"]
        self.host: str = self.config["host"]
        self.peers: list = self.config["peers"]
        self.test: str = self.config["test"]
        self.ignore_wrong_keys = self.config["ignore_keys"]

        if keyring is not None:
            self.keyring = keyring
        else:
            self.keyring = sLinDAKeyring()
            self.__aes_key = self._get_aes_key(self.config["password"])
        self.__aes_iv = self.__get_iv(self.config)

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
        except ValueError as ex:
            print("Crypto: Padding failed, probably wrong key?")
            if not self.ignore_wrong_keys:
                exit(201)
        except Exception as ex:
            if self.verbose >= 2:
                import traceback
                print(type(ex))
                print(traceback.print_exc())
            exit(200)
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
            print("Crypto #2: new AES key: %s" % aes_key)

        return aes_key

    def __get_iv(self, config: dict):
        """
        Creates an initialization vector for the AES CBC mode.
        The vector have to be the same for each peer, therefore it
        will be generated from the list of all involved host.
        :param args: all arguments
        :return:
        """
        addresses: list = deepcopy(config["peers"])
        addresses.append(config["host"])
        addresses.sort()

        # put the list into an MD5 hash to achieve the right byte size.
        iv = MD5.new(bytes(str(addresses), encoding='utf8')).digest()

        if self.verbose >= 2:
            print("Crypto #2: Initialization vector: %s" % iv)

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
