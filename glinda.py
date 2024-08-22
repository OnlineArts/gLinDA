#!/bin/env python3

from gLinDA.lib.config import Config
from gLinDA.lib.p2p import Runner
from gLinDA.lib.linda import LinDA
from gLinDA.lib.argument import Arguments


class Wrapper:
    """
    Basic wrapper that should initialize the LinDA call and the P2P network.
    """

    def __init__(self, arguments, run: bool = True):
        if arguments.test is None:

            self.config = Config(arguments, check_sanity=run).get()
            if run:
                self.run()
        else:
            from gLinDA.lib.p2p_test import P2PIsolationTester
            P2PIsolationTester(Config(arguments, check_sanity=False).get(), arguments.test)

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
        results = LinDA.run_sl_avg(replies, self.config["LINDA"]["formula"], not self.config["LINDA"]["intersection"])
        print(LinDA.display_results(results))

        return results


def main():
    """
    Performs the argument parsing.
    """
    parser = Arguments()
    Wrapper(parser.get_args())


if __name__ == "__main__":
    main()