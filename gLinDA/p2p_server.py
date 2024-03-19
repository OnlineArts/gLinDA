from p2p import P2P, Keyring, P2PPackage

import socket
import random


class Server(P2P):

    def __init__(self, config: dict, keyring: Keyring = None, initial: bool = False, results: dict = {}):
        if keyring is None:
            keyring = Keyring()
        super().__init__(config, keyring)
        self.__answers: dict = {}
        self.nr_clients: int = len(self.peers)

        if self.nr_clients == 0:
            print("No clients awaiting, terminating server")
            exit(300)

        if initial:
            self.__await_responses(self.host, self.keyring.get_peers()["R"], self.__handshake_keyring)
        else:
            self.__await_responses(self.host, self.__answers, self.__reception)
            results.update(self.__answers)

    def get_answers(self) -> dict:
        """
        Returns the messages from all participants
        :return: the messages
        """
        return self.__answers
    
    def __await_responses(self, host: str, bucket, func: object):
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

            try:
                while self.__inner_loop(s, bucket, func):
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

    def __inner_loop(self, s: socket.socket, bucket, func):
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

                if self.verbose >= 3:
                    print("Server: Current bucket size %d" % len(bucket))
                if len(bucket) >= self.nr_clients:
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
        cache: P2PPackage = P2PPackage(self.bytes_len, self.verbose)

        while not cache.stop:
            data = conn.recv(self.chunk_size)
            if not data:
                return False

            if self.verbose >= 2:
                print("Server: Got %s" % data)

            cache.load(data)

            if cache.stop:
                if self.config["asymmetric"]:
                    key = self.keyring.get_keys(True)[0]
                else:
                    self.encryption.set_init_vector(self.keyring.get_iv())
                    key = self.keyring.for_reception(cache.identifier)

                cache.msg = self.encryption.decrypt(cache.msg, key)
                bucket.update({cache.identifier: cache.msg})

                if self.verbose >= 2:
                    print("Server #2: Used key %s" % key)

        return True

    def __handshake_keyring(self, conn, addr, bucket):
        data = conn.recv(self.chunk_size)
        if not data:
            return False

        data_decrypted = self.encryption.decrypt(
            data,
            self.key
        )

        rsa_key: bytes = bytes()
        if self.config["asymmetric"] and len(data_decrypted) > self.bytes_len:
            rsa_key = data_decrypted[3:]
            data_decrypted = data_decrypted[:3]

        decrypted_number = int.from_bytes(data_decrypted, "big")

        if data_decrypted is None or not (super().min_rand <= decrypted_number <= super().max_rand):
            if self.verbose >= 1:
                print("Server #1: Received data which can not decrypted")
            return True

        if self.verbose >= 2:
            print("Server #2: Data received %s" % data_decrypted)
            print("Server #2: Decrypted number %d" % decrypted_number)

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
            confirmation_number.to_bytes(super().bytes_len, "big") + new_key, self.key
        ))

        return True
