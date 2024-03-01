from .p2p import sLinDAP2P

import socket
import random
from argparse import ArgumentParser


class sLinDAserver(sLinDAP2P):

    cache: bytes = bytes()

    def __init__(self, args: ArgumentParser, keyring: object = None, initial: bool = False):
        super().__init__(args, keyring)
        self.answers: dict = {}
        self.nr_clients: int = len(self.peers)

        if self.nr_clients == 0:
            print("No clients awaiting, terminating server")
            exit(100)

        if initial:
            self.__await_responses(self.host, self.keyring.get_peers()["R"], self.__first_contact)
        else:
            self.__await_responses(self.host, self.answers, self.__reception)
            print(self.answers)

    def __await_responses(self, host: str, bucket, func: object):
        if self.verbose >= 2:
            print('Starting server on %s' % host)
        host, port = host.split(":")

        waiting = True

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((host, int(port)))
            s.listen()

            try:
                while True:
                    if waiting:
                        waiting = self.__inner_loop(s, bucket, func)
                    else:
                        break
            except KeyboardInterrupt as e:
                s.close()
                print("Server: Closed server by manual interruption.")
            except Exception as e:
                print(e)

    def __inner_loop(self, s: socket.socket, bucket, func):
        conn, addr = s.accept()
        with conn:
            if self.verbose >= 1:
                print("Server: Client connected by %s" % str(addr))
            while True:

                # TODO: Stop does not work
                if not func(conn, addr):
                    break

                if self.verbose >= 3:
                    print("Server: Current bucket size %d" % len(bucket))
                if len(bucket) >= self.nr_clients:
                    return False
            return True

    def __get_identifier(self, data: bytes) -> int:
        identifier = int.from_bytes(bytes, "big")

        if self.verbose >= 2:
            print("Server: identifier %d" % identifier)

        return identifier

    def __get_break(self, identifier: int, potential_brake: bytes) -> bool:
        end, endid = None, None
        try:
            if self.verbose >= 3:
                print("Server: potential end %s" % potential_brake)
            end = potential_brake[:4].decode("utf8")
            endid = int.from_bytes(potential_brake[-self.bytes_len:], "big")
        except UnicodeDecodeError as e:
            pass
        except Exception as e:
            pass

        return (end is not None and endid is not None and end == "END:" and endid == identifier)

    def __reception(self, conn, addr):
        finish = False
        data = conn.recv(self.chunk_size)
        if not data:
            return False

        identifier = self.__get_identifier(data[:self.bytes_len])
        if self.verbose >= 2:
            print("Server: Got %s" % data)
        end_of_sub = self.__get_break(identifier, data[-(4+self.bytes_len):])

        if end_of_sub:
            payload = data[self.bytes_len:-(4 + self.bytes_len)]
        else:
            payload = data[self.bytes_len:]

        aes_key = self.keyring.for_reception(identifier)
        decrypted_payload: bytes = self.decrypt(payload, aes_key)
        self.cache += decrypted_payload

        if self.verbose >= 2:
            print("Server: Used key %s" % aes_key)
            print("Server: Decrypted msg %s" % decrypted_payload)

        if finish:
            if self.verbose >= 2:
                print("Server: End of submission confirmed")
            self.answers.update({identifier: self.cache})
            print(self.answers)
            return False

        return True

    def __first_contact(self, conn, addr):
        data = conn.recv(self.chunk_size)
        if not data:
            return False

        data_decrypted = super().decrypt(data)
        decrypted_number = int.from_bytes(data_decrypted, "big")
        if data_decrypted is None or not (super().min_rand <= decrypted_number <= super().max_rand):
            if self.verbose >= 1:
                print("Server: Received data which can not decrypted")
            return True

        if self.verbose >= 2:
            print("Server: Data received %s" % data_decrypted)
            print("Server: Decrypted number %d" % decrypted_number)

        confirmation_number = decrypted_number + 1
        new_key = self._get_aes_key(str(confirmation_number + random.randint(super().min_rand,super().max_rand)), True)
        self.keyring.add_peer(confirmation_number, new_key, True)

        conn.sendall(super().encrypt(confirmation_number.to_bytes(super().bytes_len, "big") + new_key))
        return True