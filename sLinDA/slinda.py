#!/bin/env python3
import socket
import random

from argparse import ArgumentParser
from Crypto.Hash import SHA512, SHA256, MD5
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad


class sLinDAWrapper:

    def __init__(self, arguments: ArgumentParser):
        self.args = arguments
        print("Awaited clients: %d" % len(self.args.p))

        if len(self.args.p) == 1 and self.args.p[0] == self.args.host:
            print("Self-Test")


        if len(self.args.test):
            if self.args.test == 'server':
                sLinDAserver(self.args)
            elif self.args.test == 'client':
                sLinDAclient(self.args)

class sLinDAP2P:

    def __init__(self, args: ArgumentParser, transformations: int = 100000):
        self.verbose = args.verbose

        self.__sha_iter = transformations
        self.__aes_key = self.__get_aes_key(args)
        self.__aes_iv = self.__get_iv(args)
        self.__test_aes("Hallo Welt!")

    def __get_aes_key(self, args: ArgumentParser):
        if self.verbose >= 2:
            print("Start SHA512 transformations iterations %d" % self.__sha_iter)
        hash = SHA512.new()
        hash.update(bytes(args.password, encoding='utf8'))
        for i in range(0, self.__sha_iter):
            hash.update(hash.digest())
        aes_key = SHA256.new(hash.digest()).digest()

        if self.verbose >= 2:
            print("AES Key: %s" % aes_key)

        return aes_key

    def __get_iv(self, args: ArgumentParser):

        addresses: list = args.p
        addresses.append(args.host)
        addresses.sort()
        iv = MD5.new(bytes(str(addresses), encoding='utf8')).digest()

        if self.verbose >= 2:
            print("Initialization vector: %s" % iv)

        return iv

    def __test_aes(self, msg: str):
        data = bytes(msg, encoding="utf8")
        cipher = AES.new(self.__aes_key, AES.MODE_CBC, iv=self.__aes_iv)
        cipher_text = cipher.encrypt(pad(data, AES.block_size))
        if self.verbose >= 1:
            print("Cipher-Text: %s" % cipher_text )
        decrypt_cipher = AES.new(self.__aes_key, AES.MODE_CBC, self.__aes_iv)
        plain_text = decrypt_cipher.decrypt(cipher_text)

        if self.verbose >= 1:
            print("Plain text: %s" % (unpad(plain_text, AES.block_size).decode('utf8')))

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

                """data = conn.recv(1024)
                if not data:
                    break

                if self.verbose >= 1:
                    print("Server: Data received %s" % str(data.decode("utf8")))
                msg: bytes = bytes('Thank you for connecting, I received %s' % data, encoding='utf8')
                conn.sendall(msg)"""
            return True, None

    def __first_contact(self, conn, addr):
        data = conn.recv(1024)
        if not data:
            return False
        if self.verbose >= 1:
            print("Server: Data received %s" % str(data.decode("utf8")))
        #msg: bytes = bytes('Thank you for connecting, I received %s' % data, encoding='utf8')
        msg: bytes = bytes('"OK"', encoding='utf8')
        conn.sendall(msg)

        self.answers.update({str(addr): str(data.decode("utf8"))})
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


class sLinDAclient(sLinDAP2P):

    def __init__(self, args: ArgumentParser):
        super().__init__(args)
        peer = args.p[0]
        self.__test(peer)

    def __test(self, peer: str):
        host, port = peer.split(":")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                random_number =  random.randint(100,999)
                if self.verbose >= 1:
                    print("Client: send random number %d" % random_number)
                msg = b'%d' % random_number
                s.connect((host, int(port)))
                s.sendall(msg)
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
    parser.add_argument("password", default=None, type=str)
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