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
                sLinDAserver(self.args.verbose, self.args.host)
            elif self.args.test == 'client':
                sLinDAclient(self.args.verbose, self.args.p[0])

class sLinDA:

    def __init__(self, verbose: int = 0):
        self.verbose = verbose

class sLinDAserver(sLinDA):

    def __init__(self, verbose: int, host: str):
        super().__init__(verbose)
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
        host, port = peer.split(":")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:

            try:
                s.connect((host, int(port)))
                s.sendall(b"Hello, world")
                data = s.recv(1024)
                if self.verbose >= 1:
                    print(f"Client: received data: {data!r}")
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

if __name__ == "__main__":
    main()