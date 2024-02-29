from .p2p import sLinDAP2P

import socket
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
            print("Server: All data received")
            print("Server: %s" % str(self.answers))

        #self.__test(host)

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

                if len(self.answers) == self.clients:
                    return False, None
            return True, None

    def __first_contact(self, conn, addr):
        data = conn.recv(1024)
        if not data:
            return False

        data_decrypted = super().decrypt_text(data)
        if self.verbose >= 2:
            print("Server: Data received %s" % data_decrypted)

        decrypt_number = int(data_decrypted)
        confirm_number = decrypt_number+1

        conn.sendall(super().encrypt_text(str(confirm_number)))

        self.answers.update({str(addr): data_decrypted})
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