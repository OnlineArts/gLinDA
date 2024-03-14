#!/bin/env python3
from config import Config
from p2p import Runner

from argparse import ArgumentParser


class Wrapper:
    """
    Basic wrapper that should initialize the LinDA call and the P2P network.
    """

    def __init__(self, arguments: ArgumentParser):
        self.config = Config(arguments).get()
        self.__p2p = Runner(self.config["P2P"])

        # Ready to use from here
        self._example_workflow()

    def _example_workflow(self):
        """
        A minimal example demonstrating how to send and receive values
        """
        import random

        # Broadcast a string
        my_msg: str = "Test Message: %s" % random.randint(10, 99)
        broadcast = self.__p2p.broadcast_str(my_msg)
        print("My message: %s" % my_msg)
        print("Received messages: %s" % broadcast)

        # Broadcast a dictionary as an object
        #my_dictionary: dict = {"OK %d" % random.randint(0, 9): "V %d" % random.randint(0, 9)}
        #broadcast = self.__p2p.broadcast_obj(my_dictionary)
        #print("My dictionary: %s" % my_dictionary)
        #print("Received messages: %s" % broadcast)


def main():
    """
    Performs the argument parsing.
    """
    parser = ArgumentParser()
    parser.add_argument("--host", help="The own host address and port")
    parser.add_argument("-pw", "--password", type=str,
                        help="Mandatory password for communication")
    parser.add_argument("-p", "--peers", nargs="+",
                        help="A list with peer addresses and ports, e.g. localhost:5000 localhost:5001")
    parser.add_argument("-t", "--test", type=str, help="Developers")
    parser.add_argument('-v', '--verbose', action='count',
                        help="Enables verbose mode, repeat v for a higher verbose mode level")
    parser.add_argument("--ignore-keys", default=False, action='store_true',
                        help="Ignores wrong keys. Will not stop execution if wrong password communication are appearing")
    parser.add_argument("--config", type=str, help="path to config file")

    args = parser.parse_args()
    Wrapper(args)


if __name__ == "__main__":
    main()