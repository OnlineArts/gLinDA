#!/bin/env python3
import random
from argparse import ArgumentParser
from threading import Thread


class sLinDAWrapper:
    """
    Manages the initialization and startring of classes.
    """

    keyring: object = None

    def __init__(self, arguments: ArgumentParser):
        """
        Initialize the server and or client class
        :param arguments: All arguments
        """
        self.args = arguments
        self.verbose = self.args.verbose
        print("Awaited clients: %d" % len(self.args.p))

        if len(self.args.p) == 1 and self.args.p[0] == self.args.host:
            print("Self-Test")

        ### FILE TRANSMISSION TEST ###
        #payload: bytes = bytes()
        #with open("/home/roman/Downloads/article-1280x720.af74a0cf.jpg", "rb") as f:
        #    r = f.read()
        #    payload += r
        #print(len(r))

        if self.args.test is not None and self.args.test == 'server':
            self.run_server()
        elif self.args.test is not None and self.args.test == 'client':
            self.run_client()
        else:
            keyring = self._start_initialization_round()
            if len(keyring) != (2 * len(self.args.p)):
                print("Keyring incomplete, could not chat with every peer!")
                exit(101)
            elif self.verbose >= 2:
                print(keyring.get_peers())
            elif self.verbose >= 1:
                print("Keyring is complete!")

            self.keyring = keyring
            payload = ""
            server, data = self._broadcast_round(payload)

    def _start_initialization_round(self):
        print("Starting server in a separate thread")
        thread = Thread(target=self.run_server, args=(True,))
        thread.start()
        client = self.run_client(True)
        thread.join()
        if self.verbose >= 1:
            print("==> Client and server are finished.")
        return client.keyring

    def _broadcast_round(self, payload: bytes):
        if self.args.test is not None and self.args.test == "r2client":
            client = self.run_client()
            msg: str = "Test Message: %s" % random.randint(10,99)
            load: bytes = msg.encode("utf8")
            client.send_payload(load)
            return None, bytes(0)
        elif self.args.test is not None and self.args.test == "r2server":
            server = self.run_server()
            return server, bytes(0)

    def run_server(self, initial: bool = False):
        """
        Loads the P2P Server class, that is listening.
        :return: the server class object
        """
        from lib.p2p_server import sLinDAserver
        server = sLinDAserver(self.args, self.keyring, initial)
        return server

    def run_client(self, initial: bool = False):
        """
        Loads the P2P Client class, that submits data.
        :return: the client class object
        """
        from lib.p2p_client import sLinDAclient
        client = sLinDAclient(self.args, self.keyring, initial)
        return client


def main():
    """
    Performs the argument parsing.
    """
    parser = ArgumentParser()
    parser.add_argument("host", default="localhost:5000")
    parser.add_argument("password", default=None, type=str)
    parser.add_argument("-p", "-peer", nargs="+", default=["localhost:5000"])
    parser.add_argument("-t", "--test", type=str, default=None)
    parser.add_argument('-v', '--verbose', action='count', default=0,
                        help="enable verbose mode, repeat v for a higher verbose mode level")

    args = parser.parse_args()
    sLinDAWrapper(args)


if __name__ == "__main__":
    main()