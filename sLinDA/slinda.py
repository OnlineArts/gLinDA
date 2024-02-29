#!/bin/env python3
from argparse import ArgumentParser


class sLinDAWrapper:

    def __init__(self, arguments: ArgumentParser):
        self.args = arguments
        print("Awaited clients: %d" % len(self.args.p))

        if len(self.args.p) == 1 and self.args.p[0] == self.args.host:
            print("Self-Test")

        if len(self.args.test):
            if self.args.test == 'server':
                from lib.p2p_server import sLinDAserver
                sLinDAserver(self.args)
            elif self.args.test == 'client':
                from lib.p2p_client import sLinDAclient
                sLinDAclient(self.args)


def main():
    parser = ArgumentParser()
    parser.add_argument("host", default="localhost:5000")
    parser.add_argument("password", default=None, type=str)
    parser.add_argument("-p", "-peer", nargs="+", default=["localhost:5000"])
    parser.add_argument("-t", "--test", type=str, default="")
    parser.add_argument('-v', '--verbose', action='count', default=0,
                        help="enable verbose mode, repeat v for a higher verbose mode level")

    args = parser.parse_args()
    sLinDAWrapper(args)

if __name__ == "__main__":
    main()