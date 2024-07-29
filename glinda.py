#!/bin/env python3
from argparse import ArgumentParser

from gLinDA.lib.config import Config
from gLinDA.lib.p2p import Runner
from gLinDA.lib.linda import LinDA


class Wrapper:
    """
    Basic wrapper that should initialize the LinDA call and the P2P network.
    """

    def __init__(self, arguments: ArgumentParser, run: bool = True):
        self.config = Config(arguments, check_sanity=run).get()

        if run:
            self.run()

    def run(self):
        if ("solo_mode" in self.config["P2P"] and self.config["P2P"]["solo_mode"]) or self.config["P2P"]["host"] is None:
            return self.run_locally()
        else:
            return self.run_sl()

    def run_locally(self):
        results = LinDA.run_local(self.config["LINDA"])
        print(LinDA.display_results(results))

        return results

    def run_sl(self):

        # calculate coefficients
        coeffs = LinDA.run_sl(self.config["LINDA"])

        # start and broadcast p2p network
        p2p = Runner(self.config["P2P"])
        replies = p2p.broadcast_obj(coeffs)

        # Add own parameters to the replies
        replies.update({0: coeffs})
        results = LinDA.run_sl_avg(replies, self.config["LINDA"]["formula"])
        print(LinDA.display_results(results))

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