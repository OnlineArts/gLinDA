from pickle import loads, dumps
from threading import Thread
from copy import deepcopy

from Crypto.Hash import MD5, SHA256, SHA512
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Util.Padding import pad, unpad

"""
gLinDAP2P

This parent package carries all required code for the peer-to-peer network, including the multi-threaded 
implementation and all cryptographic-related handling.
"""

__version__ = "0.9.0"
__author__ = 'Roman Martin'
__credits__ = 'Heinrich Heine University Duesseldorf'


class gLinDAKeyring:

    _peers: dict = {
        "R": {},    # keys for receiving data
        "S": {}     # keys for submitting data
    }
    _keys: dict = {
        "S": (),
        "C": ()
    }
    _iv = None

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

    def get_iv(self):
        return self._iv

    def set_iv(self, init_vector: bytes):
        self._iv = init_vector

    def set_keys(self, private: bytes, public: bytes, server: bool = True):
        self._keys["S" if server else "C"] = (private, public)

    def get_keys(self, server: bool = True) -> dict:
        return self._keys["S" if server else "C"]


class P2P:

    min_rand: int = 1000000
    max_rand: int = 9999999
    bytes_len: int = 3
    waiting_time: int = 2
    chunk_size: int = 1024000
    symmetric = False

    def __init__(self, config: dict, keyring: gLinDAKeyring = None):
        self.keyring = keyring
        self.config: dict = config
        self.verbose: int = self.config["verbose"]
        self.host: str = self.config["host"]
        self.peers: list = self.config["peers"]
        self.ignore_wrong_keys = self.config["ignore_keys"]

        if "asymmetric" in self.config and self.config["asymmetric"]:
            self.encryption = EncryptionAsymmetric()
        else:
            self.encryption = EncryptionSymmetric()

        if not len(keyring):
            # Create asymmetric keys
            if self.config["asymmetric"]:
                private_key, public_key = EncryptionAsymmetric().get_key(verbose=self.verbose >= 1)
                self.keyring.set_keys(private_key, public_key, True)
                private_key, public_key = EncryptionAsymmetric().get_key(verbose=self.verbose >= 1)
                self.keyring.set_keys(private_key, public_key, False)

            # initially symmetric encryption
            self.encryption = EncryptionSymmetric()

            self.key = self.encryption.get_key(self.config["password"], self.verbose >= 2)
            # Only for symmetric encryption required
            if isinstance(self.encryption, EncryptionSymmetric):
                self.keyring.set_iv(self.encryption.get_iv(self.config, self.verbose >= 2))


class EncryptionSymmetric:

    @staticmethod
    def encrypt(data: bytes, aes_key: bytes, init_vector: bytes) -> bytes:
        """
        Encrypts and pads raw bytes data into a cipher.
        :param data: the raw data
        :param aes_key: optionally, an alternative AES key
        :return: the cipher
        """
        cipher = AES.new(aes_key, AES.MODE_CBC, iv=init_vector)
        cipher_text = cipher.encrypt(pad(data, AES.block_size))
        return cipher_text

    @staticmethod
    def decrypt(ciper: bytes, aes_key: bytes, init_vector: bytes, ignore_wrong_keys: bool = True) -> bytes:
        """
        Decrypts and unpads a ciper to raw data
        :param ciper: the cipher
        :param aes_key: optionally, an alternative AES key
        :return: the raw data
        """
        decrypt_cipher = AES.new(aes_key, AES.MODE_CBC, init_vector)
        data = decrypt_cipher.decrypt(ciper)
        unpadded = None
        try:
            unpadded = unpad(data, AES.block_size)
        except ValueError as ex:
            print("Crypto: Padding failed, probably wrong key?")
            if not ignore_wrong_keys:
                exit(201)
        except Exception as ex:
            import traceback
            print(type(ex))
            print(traceback.print_exc())
            exit(200)
        return unpadded

    @staticmethod
    def get_key(password: str, verbose: bool = True, iterations: int = 100000, skip_iterations: bool = False):
        """
        Generates from the password (over single or multiple iterations of hashing) an AES key.
        :param password: the shared password
        :param skip_iterations: if True, performs n iterations of hashing
        :return: the AES key
        """
        hash = SHA512.new()
        hash.update(bytes(password, encoding='utf8'))
        if not skip_iterations:
            if verbose:
                print("EncryptionSymmetric: Start SHA512 transformations iterations %d" % iterations)
            for i in range(0, iterations):
                hash.update(hash.digest())
        aes_key = SHA256.new(hash.digest()).digest()

        if verbose:
            print("EncryptionSymmetric: new AES key: %s" % aes_key)

        return aes_key

    @staticmethod
    def get_iv(config: dict, verbose: bool = True):
        """
        Creates an initialization vector for the AES CBC mode
        The vector have to be the same for each peer, therefore it
        will be generated from the list of all involved host
        :param args: all arguments
        :return:
        """
        addresses: list = deepcopy(config["peers"])
        addresses.append(config["host"])
        addresses.sort()

        # put the list into an MD5 hash to achieve the right byte size.
        iv = MD5.new(bytes(str(addresses), encoding='utf8')).digest()

        if verbose:
            print("EncryptionSymmetric: Initialization vector: %s" % iv)

        return iv


class EncryptionAsymmetric:

    @staticmethod
    def encrypt(data: bytes, public_key: bytes, init_vector: bytes = None) -> bytes:
        recipient_key = RSA.importKey(public_key)
        cipher_rsa = PKCS1_OAEP.new(recipient_key)
        encrypted_msg = cipher_rsa.encrypt(data)
        return encrypted_msg

    @staticmethod
    def decrypt(cipher: bytes, private_key: bytes, init_vector: bytes = None, ignore_wrong_keys: bool = True) -> bytes:
        private_key = RSA.importKey(private_key)
        ciper_rsa = PKCS1_OAEP.new(private_key)
        msg = ciper_rsa.decrypt(cipher)
        return msg

    @staticmethod
    def get_key(bits: int = 1024, verbose: bool = True) -> tuple:
        key = RSA.generate(bits)
        if verbose:
            print("EncryptionAsymmetric: Create public and private RSA keys")
        return key.export_key(), key.public_key().export_key()


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
        :param as_list: if False participants data will be provided as a dictionary
        :return: list or dictionary with the values from the other participants
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
        if "test" in self.config and self.config["test"] == "r2client":
            client = self.run_client()
            client.send_payload(payload)
            return None
        elif "test" in self.config and self.config["test"] == "r2server":
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
        if "test" in self.config is not None and self.config["test"] == 'server':
            server = self.run_server(True)
            print( server.keyring.get_peers() )
            exit(0)
        elif "test" in self.config is not None and self.config["test"] == 'client':
            client = self.run_client(True)
            print( client.keyring.get_peers() )
            exit(0)
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
        from p2p_server import gLinDAserver
        server = gLinDAserver(self.config, self.keyring, initial, results)
        return server

    def run_client(self, initial: bool = False):
        """
        Loads the P2P Client class, that submits data.
        :return: the client class object
        """
        from p2p_client import gLinDAclient
        client = gLinDAclient(self.config, self.keyring, initial)
        return client

class P2PPackage:
    
    header: bytes = bytes()
    msg: bytes = bytes()
    stop: bytes = bytes()

    def load(self):
        pass

    def get(self):
        pass
