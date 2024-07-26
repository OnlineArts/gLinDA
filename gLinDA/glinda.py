#!/bin/env python3
from argparse import ArgumentParser

from gLinDA.lib.config import Config
from gLinDA.lib.p2p import Runner
from gLinDA.lib.linda import LinDA


class Wrapper:
    """
    Basic wrapper that should initialize the LinDA call and the P2P network.
    """

    def __init__(self, arguments: ArgumentParser):
        self.config = Config(arguments).get()

        if ("solo_mode" in self.config["P2P"] and self.config["P2P"]["solo_mode"]) or self.config["P2P"]["host"] is None:
            self.run_locally()
        else:
            self.__p2p = Runner(self.config["P2P"])
            self.run_sl()

    def run_locally(self):
        linda = LinDA()
        results = linda.run_local(self.config["LINDA"])
        print(results)
        return results

    def run_sl(self):
        linda = LinDA()
        coeffs = linda.run_sl_start(self.config["LINDA"])
        replies = self.__p2p.broadcast_obj(coeffs)
        # Add own parameters to the replies
        replies.update({0: coeffs})
        results = linda.run_sl_avg(replies, self.config["LINDA"]["formula"])
        print(results)
        return results


def main():
    """
    Performs the argument parsing.
    """
    parser = ArgumentParser()
    parser.add_argument("--host", help="The own host address and port")
    parser.add_argument("-pw", "--password", type=str, help="Mandatory password for communication")
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