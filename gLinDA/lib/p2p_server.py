from threading import Event
import socket
import random

from gLinDA.lib.p2p import P2P, Keyring
from gLinDA.lib.p2p_pkg import P2PCollector, P2PPackage


class Server(P2P):

    def __init__(self, config: dict, keyring: Keyring = None, initial: bool = False,
                 results: dict = {}, event: Event = None):
        if keyring is None:
            keyring = Keyring()
        super().__init__(config, keyring)
        self.__answers: dict = {}
        self.nr_clients: int = len(self.peers)
        self.event = event
        self.cache = P2PCollector(self.bytes_len, self.verbose, len(self.config["peers"]))

        if self.nr_clients == 0:
            print("No clients awaiting, terminating server")
            exit(300)

        if initial:
            self.__await_responses(self.host, self.keyring.get_peers()["R"], self.__handshake_keyring, initial)
        elif not self.cache.is_finished():
            self.__await_responses(self.host, self.__answers, self.__reception, initial)
            for peer in self.cache.identifiers.keys():
                raw_msg = self.cache.get_payload(peer)

                if self.config["asymmetric"]:
                    decrypt_key = self.keyring.get_keys(True)[0]
                else:
                    self.encryption.set_init_vector(self.keyring.get_iv())
                    decrypt_key = self.keyring.for_reception(peer)

                if self.verbose >= 2:
                    print("Server #2: Use decryption key %s" % decrypt_key)

                msg = self.encryption.decrypt(raw_msg, decrypt_key)
                results.update({peer: msg})

    def get_answers(self) -> dict:
        """
        Returns the messages from all participants
        :return: the messages
        """
        return self.__answers
    
    def __await_responses(self, host: str, bucket, func: object, initial: bool = False):
        """
        Basic backbone for the host connection
        :param host: the own host address
        :param bucket: a bucket functions as a cache
        :param func: an object function, that will be executed inside as a first outer loop
        :return:
        """

        if self.verbose >= 2:
            print('Starting server on %s' % host)
        host, port = host.split(":")

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((host, int(port)))
            s.listen()

            if self.event is not None:  # only for multithreaded call
                self.event.set()

            try:
                while self.__inner_loop(s, bucket, func, initial):
                    pass
            except KeyboardInterrupt as e:
                s.close()
                print("Server: Closed server by manual interruption.")
            except Exception as e:
                if self.verbose >= 2:
                    import traceback
                    print(type(e))
                    print(traceback.print_exc())
                print(e)

    def __inner_loop(self, s: socket.socket, bucket, func, initial: bool = False):
        """
        The inner function to execute in the outer loop.
        :param s: the socket connection
        :param bucket: a bucket functions as a cache
        :param func: an object function, that will be executed inside as a first outer loop
        :return:
        """
        conn, addr = s.accept()
        with conn:
            if self.verbose >= 1:
                print("Server: Client connected by %s" % str(addr))
            while True:

                if self.verbose >= 3 and initial:
                    print("Server: Current bucket size %d" % len(bucket))

                if (initial and len(bucket) >= self.nr_clients) or (not initial and self.cache.is_finished()):
                    return False

                if not func(conn, addr, bucket):
                    break

            return True

    def __reception(self, conn, addr, bucket) -> bool:
        """
        An inner function that manages incoming messages.
        :param conn: the established socket to host connection
        :param addr: the users address
        :param bucket: a variable cache
        :return: True after termination
        """

        while not self.cache.is_finished():
            data = conn.recv(self.chunk_size)
            if not data:
                return False

            if self.verbose >= 2:
                print("Server #2: Got (%d) %s" % (len(data), data))

            pkg = P2PPackage(self.bytes_len, self.verbose)

            if not pkg.load(data):
                print("Server: Can not load package.")
                return True

            self.cache.load(pkg)

            if self.cache.is_finished():
                bucket.update({pkg.get_identifier(): self.cache.get_payload(pkg.get_identifier())})

        return True

    def __handshake_keyring(self, conn, addr, bucket):
        data = conn.recv(self.chunk_size)
        if not data:
            return False

        init_aes_key = self.get_init_key()

        if self.verbose >= 3:
            print("ServerHandshake #3: Data received %s" % data)
            print("ServerHandshake #3: Use decryption key %s" % init_aes_key)

        data_decrypted = self.encryption.decrypt(
            data,
            init_aes_key
        )

        rsa_key: bytes = bytes()
        if self.config["asymmetric"] and len(data_decrypted) > self.bytes_len:
            rsa_key = data_decrypted[3:]
            data_decrypted = data_decrypted[:3]

        decrypted_number = int.from_bytes(data_decrypted, "big")

        if data_decrypted is None or not (super().min_rand <= decrypted_number <= super().max_rand):
            if self.verbose >= 1:
                print("ServerHandshake #1: Received data which can not decrypted")
            return True

        if self.verbose >= 2:
            print("ServerHandshake #2: Data decrypted received %s" % data_decrypted)
            print("ServerHandshake #2: Decrypted number %d" % decrypted_number)

        confirmation_number = decrypted_number + 1

        # RSA
        if self.config["asymmetric"] and len(rsa_key):
            new_key = self.keyring.get_keys(True)[1]
            self.keyring.add_peer(confirmation_number, rsa_key)
        # AES
        else:
            key_str = str(confirmation_number + random.randint(super().min_rand, super().max_rand))
            new_key = self.encryption.get_key(key_str, self.verbose >= 2)
            self.keyring.add_peer(confirmation_number, new_key, True)

        conn.sendall(self.encryption.encrypt(
            confirmation_number.to_bytes(self.bytes_len, "big") + new_key, init_aes_key))

        return True
