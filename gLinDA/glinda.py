#!/bin/env python3
from gLinDA.config import gLinDAConfig
from gLinDA.p2p import gLinDAP2Prunner

from argparse import ArgumentParser

class gLinDAWrapper:

    def __init__(self, arguments: ArgumentParser):
        self.config = gLinDAConfig(arguments).get()
        self.__p2p = gLinDAP2Prunner(self.config["P2P"])
        self._example_workflow()

    def _example_workflow(self):
        import random

        # Broadcast a string
        broadcast = self.__p2p.broadcast_str("Test Message: %s" % random.randint(10, 99))
        print(broadcast)

        # Broadcast a dictionary as an object
        broadcast = self.__p2p.broadcast_obj({"OK %d" % random.randint(0, 9): "V %d" % random.randint(0, 9)})
        print(broadcast)


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
    gLinDAWrapper(args)


if __name__ == "__main__":
    main()