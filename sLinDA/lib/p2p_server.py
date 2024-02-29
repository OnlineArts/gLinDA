from .p2p import sLinDAP2P

import socket
import random
from argparse import ArgumentParser


class sLinDAserver(sLinDAP2P):

    def __init__(self, args: ArgumentParser):
        super().__init__(args)
        host = args.host
        clients = len(args.p)

        if clients == 0:
            print("No clients awaiting, terminating server")
            exit(100)

        self.answers: dict = {}
        self.clients: int = clients
        self.__await_responses(host)

        if self.verbose >= 1:
            print("Server: All keys received")
            print("Server: %s" % self.keyring.get_peers())

    def __await_responses(self, host: str):
        host, port = host.split(":")

        waiting = True
        func = self.__first_contact

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((host, int(port)))
            s.listen()

            try:
                while True:
                    if waiting:
                        waiting, response = self.__basic_inner_loop(s, func)
                    else:
                        break
            except KeyboardInterrupt as e:
                s.close()
                print("Server: Closed server by manual interruption.")
            except Exception as e:
                print(e)

    def __basic_inner_loop(self, s: socket.socket, func):
        conn, addr = s.accept()
        with conn:
            if self.verbose >= 1:
                print("Server: Client connected by %s" % str(addr))
            while True:

                if not func(conn, addr):
                    break

                if self.verbose >= 3:
                    print("Server: Current keyring size %d" % len(self.keyring.get_peers()["R"]))
                if len(self.keyring.get_peers()["R"]) >= self.clients-1:
                    return False, None
            return True, None

    def __first_contact(self, conn, addr):
        data = conn.recv(1024)
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
        new_key = self._get_aes_key(str(confirmation_number + random.randint(super().min_rand,super().max_rand)))
        self.keyring.add_peer(confirmation_number, new_key, True)

        conn.sendall(super().encrypt(confirmation_number.to_bytes(super().bytes_len, "big") + new_key))
        return True

    def __test(self, host):
        host, port = host.split(":")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((host, int(port)))
            s.listen()

            try:
                while True:
                    conn, addr = s.accept()
                    with conn:
                        if self.verbose >= 1:
                            print("Server: Client connected by %s" % str(addr))
                        while True:
                            data = conn.recv(1024)
                            if not data:
                                break
                            if self.verbose >= 1:
                                print("Server: Data received %s" % str(data.decode("utf8")))
                            msg: bytes = bytes('Thank you for connecting, I received %s' % data, encoding='utf8')
                            conn.sendall(msg)
            except KeyboardInterrupt as e:
                s.close()
                print("Server: Closed server by manual interruption.")
            except Exception as e:
                print(e)