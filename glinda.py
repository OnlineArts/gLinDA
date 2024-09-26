#!/bin/env python3
import os.path

from gLinDA.lib.config import Config
from gLinDA.lib.p2p import Runner
from gLinDA.lib.linda import LinDA
from gLinDA.lib.argument import Arguments

__version__ = "1.0.0"

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
        self.export_result(results)
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
        self.export_result(results)
        print(LinDA.display_results(results))

        return results

    def export_result(self, results):
        try:
            if type(self.config["LINDA"]["output"]) is str and len(self.config["LINDA"]["output"]):
                prefix = os.path.basename(self.config["LINDA"]["feature_table"])
                prefix = prefix[:prefix.rfind(".")]
                LinDA.export_results(results, self.config["LINDA"]["output"], prefix )
        except:
            print("Can not store results at the given path")

def main():
    """
    Performs the argument parsing.
    """
    parser = Arguments()
    Wrapper(parser.get_args())


if __name__ == "__main__":
    main()