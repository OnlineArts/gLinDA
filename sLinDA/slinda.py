#!/bin/env python3
import socket
from argparse import ArgumentParser

class sLinDAWrapper:

    def __init__(self, arguments: ArgumentParser):
        self.args = arguments

        if len(self.args.p) == 1 and self.args.p[0] == self.args.host:
            print("Self-Test")

        if len(self.args.test):
            if self.args.test == 'server':
                sLinDAserver(self.args.verbose, self.args.host, len(self.args.p))
            elif self.args.test == 'client':
                sLinDAclient(self.args.verbose, self.args.p[0])

class sLinDA:

    def __init__(self, verbose: int = 0):
        self.verbose = verbose

class sLinDAserver(sLinDA):

    def __init__(self, verbose: int, host: str, clients: int = 0):
        super().__init__(verbose)

        if clients == 0:
            print("No clients awaiting, terminating server")
            exit(100)
        self.__await_responses(host, clients)
        #self.__test(host)

    def __await_responses(self, host: str, clients: int):
        answers: dict = {}
        host, port = host.split(":")

        waiting = True
        func = self.__first_contact

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
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

                if not func(conn):
                    break

                """data = conn.recv(1024)
                if not data:
                    break

                if self.verbose >= 1:
                    print("Server: Data received %s" % str(data.decode("utf8")))
                msg: bytes = bytes('Thank you for connecting, I received %s' % data, encoding='utf8')
                conn.sendall(msg)"""
        return True, None

    def __first_contact(self, conn):
        data = conn.recv(1024)
        if not data:
            return False

        if self.verbose >= 1:
            print("Server: Data received %s" % str(data.decode("utf8")))
        msg: bytes = bytes('Thank you for connecting, I received %s' % data, encoding='utf8')
        conn.sendall(msg)
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


class sLinDAclient(sLinDA):

    def __init__(self, verbose: int, peer: str):
        super().__init__(verbose)
        self.__test(peer)

    def __test(self, peer: str):
        host, port = peer.split(":")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.connect((host, int(port)))
                s.sendall(b"Hello, world")
                data = s.recv(1024)
                if self.verbose >= 1:
                    print("Client: received data: %s" % str(data.decode('utf8')))
                s.close()
            except ConnectionRefusedError as e:
                print("Error: Connection refused by the peer")
                print("Are you sure the peer is reachable?")
            except Exception as e:
                print(e)


def main():
    parser = ArgumentParser()
    parser.add_argument("host", default="localhost:5000")
    parser.add_argument("-p", "-peer", nargs="+", default=["localhost:5000"])
    parser.add_argument("-t", "--test", type=str, default="")
    parser.add_argument('-v', '--verbose', action='count', default=0,
                        help="enable verbose mode, repeat v for a higher verbose mode level")

    args = parser.parse_args()
    sLinDAWrapper(args)

# aes
"""
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

data = b'secret data'

key = get_random_bytes(16)
cipher = AES.new(key, AES.MODE_EAX)
ciphertext, tag = cipher.encrypt_and_digest(data)
nonce = cipher.nonce

cipher = AES.new(key, AES.MODE_EAX, nonce)
data = cipher.decrypt_and_verify(ciphertext, tag)
"""

if __name__ == "__main__":
    main()