#!/bin/env python3
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

        if self.args.test is not None:
            if self.args.test == 'server':
                self.run_server()
            elif self.args.test == 'client':
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
            self._broadcast_round()

    def _start_initialization_round(self):
        print("Starting server in a separate thread")
        thread = Thread(target=self.run_server)
        thread.start()
        client = self.run_client()
        thread.join()
        if self.verbose >= 1:
            print("==> Client and server are finished.")
        return client.keyring

    def _broadcast_round(self):
        server = self.run_server()

    def run_server(self):
        """
        Loads the P2P Server class, that is listening.
        :return: the server class object
        """
        from lib.p2p_server import sLinDAserver
        server = sLinDAserver(self.args, self.keyring)
        return server

    def run_client(self):
        """
        Loads the P2P Client class, that submits data.
        :return: the client class object
        """
        from lib.p2p_client import sLinDAclient
        client = sLinDAclient(self.args, self.keyring)
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