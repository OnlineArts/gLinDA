#!/bin/env python3
import socket
from argparse import ArgumentParser

class sLinDA:

    def __init__(self, arguments: ArgumentParser):
        self.args = arguments

        #
        if len(self.args.test):
            if self.args.test == 'server':
                sLinDAserver(self.args.host)
            elif self.args.test == 'client':
                sLinDAclient(self.args.p[0])
        #
        if len(self.args.p) == 1 and self.args.p[0] == self.args.host:
            print("Self-Test")

class sLinDAserver:

    def __init__(self, host: str):
        host, port = host.split(":")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((host, int(port)))
            s.listen()
            conn, addr = s.accept()
            with conn:
                print(f"Connected by {addr}")
                while True:
                    data = conn.recv(1024)
                    if not data:
                        break
                    conn.sendall(data)

class sLinDAclient:

    def __init__(self, peer: str):
        host, port = peer.split(":")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, int(port)))
            s.sendall(b"Hello, world")
            data = s.recv(1024)

        print(f"Received {data!r}")


def main():
    parser = ArgumentParser()
    parser.add_argument("host", default="localhost:5000")
    parser.add_argument("-p", "-peer", nargs="+", default=["localhost:5000"])
    parser.add_argument("-t", "--test", type=str, default="")
    args = parser.parse_args()
    sLinDA(args)

if __name__ == "__main__":
    main()