from pickle import loads, dumps
from threading import Thread
from copy import deepcopy
from Crypto.Hash import MD5, SHA256, SHA512
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

"""
gLinDAP2P

This parent package carries all required code for the peer-to-peer network, including the multi-threaded 
implementation and all cryptographic-related handling.
"""

__version__ = "0.9.0"
__author__ = 'Roman Martin'
__credits__ = 'Heinrich Heine University Duesseldorf'


class gLinDAP2P:

    sha_iter: int = 100000
    min_rand: int = 1000000
    max_rand: int = 9999999
    bytes_len: int = 3
    waiting_time: int = 2
    chunk_size: int = 1024000

    def __init__(self, config: dict, keyring: object = None):
        self.config: dict = config
        self.verbose: int = self.config["verbose"]
        self.host: str = self.config["host"]
        self.peers: list = self.config["peers"]
        self.test: str = self.config["test"]
        self.ignore_wrong_keys = self.config["ignore_keys"]

        if keyring is not None:
            self.keyring = keyring
        else:
            self.keyring = gLinDAKeyring()
            self.__aes_key = self._get_aes_key(self.config["password"])
        self.__aes_iv = self.__get_iv(self.config)

    def encrypt(self, data: bytes, aes_key: bytes = None) -> bytes:
        """
        Encrypts and pads raw bytes data into a cipher.
        :param data: the raw data
        :param aes_key: optionally, an alternative AES key
        :return: the cipher
        """
        if aes_key is None:
            key = self.__aes_key
        else:
            key = aes_key
        cipher = AES.new(key, AES.MODE_CBC, iv=self.__aes_iv)
        cipher_text = cipher.encrypt(pad(data, AES.block_size))
        return cipher_text

    def decrypt(self, ciper: bytes, aes_key: bytes = None) -> bytes:
        """
        Decrypts and unpads a ciper to raw data
        :param ciper: the cipher
        :param aes_key: optionally, an alternative AES key
        :return: the raw data
        """
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
        """
        Generates from the password (over single or multiple iterations of hashing) an AES key.
        :param password: the shared password
        :param skip_iterations: if True, performs n iterations of hashing.
        :return: the AES key
        """
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


class gLinDAP2Prunner:

    keyring: object = None

    def __init__(self, config: dict):
        self.config = config
        self.verbose = config["verbose"]

        if self.verbose >= 1:
            print("Awaited clients: %d" % len(self.config["peers"]))

        self.__initialize_keyring()

    def broadcast_str(self, string: str) -> list:
        """
        Broadcast a string and receives a list of strings
        :param string: the massage submitted from this participant
        :return: a list of strings from the other participants
        """
        return self.broadcast(string, lambda e: str(e).encode("utf8"),
                              lambda d: bytes(d).decode("utf8"))

    def broadcast_obj(self, object: object) -> list:
        """
        Broadcast an object and receives a list of objects
        :param object: the data object submitted from this participant
        :return: a list of data from the other participants
        """
        return self.broadcast(object, lambda e: dumps(e), lambda d: loads(d), False)

    def broadcast(self, data, encode: callable, decode: callable, as_list: bool = True) -> list:
        """
        Submits and receives all types of data. data will be encoded prior submission by the encode function and
        all participants datas will be decoded by the decode function.
        :param data: the data that will be broadcast
        :param encode: an encoding function, should encode data and return byte arrays
        :param decode: a decoding function, decoding bytes into the desired data type
        :param as_list: if False participants data will be provided in dictionaries instead of a list
        :return: list or dictionary with the values from the other participants.
        """
        bucket = [] if as_list else {}
        bytes_coded_data: bytes = encode(data)
        reception = self.broadcast_raw(bytes_coded_data)

        for submitter in reception.keys():
            bucket.append(decode(reception[submitter])) if as_list else (
                bucket.update({submitter: decode(reception[submitter])}))

        return bucket

    def broadcast_raw(self, payload: bytes):
        """
        The native function performing broadcasting and collecting in a multi-threaded fashion.
        :param payload: the data to broadcast
        :return: a dictionary with all participants results
        """
        if self.config["test"] is not None and self.config["test"] == "r2client":
            client = self.run_client()
            client.send_payload(payload)
            return None
        elif self.config["test"] is not None and self.config["test"] == "r2server":
            server = self.run_server()
            return server.get_answers()
        else:
            if self.verbose >= 1:
                print("gLinDA: Starting server in a separate thread for broadcasting")
            results: dict = {}
            thread = Thread(target=self.run_server, args=(False, results))
            thread.start()
            client = self.run_client()
            client.send_payload(payload)
            thread.join()
            if self.verbose >= 1:
                print("=> Broadcasting finished")
            return results

    def __initialize_keyring(self):
        """
        Manages the handshake and errors; analyses the constructed keyring.
        """
        if self.config["test"] is not None and self.config["test"] == 'server':
            self.run_server()
        elif self.config["test"] is not None and self.config["test"] == 'client':
            self.run_client()
        else:
            keyring = self.__initialize_handshake()
            if len(keyring) != (2 * len(self.config["peers"])):
                print("Keyring incomplete, could not chat with every peer!")
                exit(101)
            elif self.verbose >= 2:
                print(keyring.get_peers())
            elif self.verbose >= 1:
                print("Keyring is complete!")
            self.keyring = keyring

    def __initialize_handshake(self):
        """
        Runs the multi-thread initialization, handshaking.
        :return: return a full keyring
        """
        print("Starting server in a separate thread for handshaking")
        thread = Thread(target=self.run_server, args=(True,))
        thread.start()
        client = self.run_client(True)
        thread.join()
        if self.verbose >= 1:
            print("==> Handshake complete!")
        return client.keyring

    def run_server(self, initial: bool = False, results: dict = {}):
        """
        Loads the P2P Server class, that is listening.
        :return: the server class object
        """
        from gLinDA.lib.p2p_server import gLinDAserver
        server = gLinDAserver(self.config, self.keyring, initial, results)
        return server

    def run_client(self, initial: bool = False):
        """
        Loads the P2P Client class, that submits data.
        :return: the client class object
        """
        from gLinDA.lib.p2p_client import gLinDAclient
        client = gLinDAclient(self.config, self.keyring, initial)
        return client


class gLinDAKeyring:

    _peers: dict = {
        "R": {},    # keys for receiving data
        "S": {}     # keys for submitting data
    }

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
