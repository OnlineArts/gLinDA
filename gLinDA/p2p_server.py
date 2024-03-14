from p2p import P2P, gLinDAKeyring, EncryptionAsymmetric

import socket
import random


class gLinDAserver(P2P):

    def __init__(self, config: dict, keyring: gLinDAKeyring = None, initial: bool = False, results: dict = {}):
        if keyring is None:
            keyring = gLinDAKeyring()
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
        return self.__answers

    def __await_responses(self, host: str, bucket, func: object):
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

    def __get_identifier(self, data: bytes) -> int:

        if self.verbose >= 3:
            print("Server #3: potential binary identifier %s" % data)

        try:
            identifier = int.from_bytes(data, "big")
        except TypeError:
            return 0

        if self.verbose >= 3:
            print("Server #3: identifier %d" % identifier)

        return identifier

    def __get_break(self, identifier: int, potential_brake: bytes) -> bool:
        end, endid = None, None
        try:
            end = potential_brake[:4].decode("utf8")
            endid = int.from_bytes(potential_brake[-self.bytes_len:], "big")

            if self.verbose >= 3:
                print("Server #3: expected identifier %d" % identifier)
                print("Server #3: potential end %s" % potential_brake)
                print("Server #3: end '%s'" % end)
                print("Server #3: endid '%d'" % endid)

        except UnicodeDecodeError as e:
            print(e)
            return False
        except Exception as e:
            print(e)
            return False
        return (end is not None and endid is not None) and (end == "END:" and endid == identifier)

    def __reception(self, conn, addr, bucket):
        finish: bool = False
        cache: bytes = bytes()

        while not finish:
            data = conn.recv(self.chunk_size)
            if not data:
                return False

            identifier = self.__get_identifier(data[:self.bytes_len])
            if self.verbose >= 2:
                print("Server: Got %s" % data)
            end_of_sub = self.__get_break(identifier, data[-(4+self.bytes_len):])

            if end_of_sub:
                payload = data[self.bytes_len:-(4 + self.bytes_len)]
                finish = True
            else:
                payload = data[self.bytes_len:]

            if self.config["asymmetric"]:
                key = self.keyring.get_keys(True)[0]
            else:
                key = self.keyring.for_reception(identifier)

            decrypted_payload: bytes = self.encryption.decrypt(
                payload,
                key,
                self.keyring.get_iv()
            )
            cache += decrypted_payload

            if self.verbose >= 2:
                print("Server #2: Used key %s" % key)
                print("Server #2: Decrypted data %s" % decrypted_payload)

            if finish:
                if self.verbose >= 2:
                    print("Server #2: End of submission confirmed")
                bucket.update({identifier: cache})

        return True

    def __handshake_keyring(self, conn, addr, bucket):
        data = conn.recv(self.chunk_size)
        if not data:
            return False

        data_decrypted = self.encryption.decrypt(
            data,
            self.key,
            self.keyring.get_iv()
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
            confirmation_number.to_bytes(super().bytes_len, "big") + new_key,
            self.key,
            self.keyring.get_iv()
        ))

        return True
