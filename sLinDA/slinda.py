#!/bin/env python3
import random
import pickle
from argparse import ArgumentParser
from threading import Thread


class sLinDAWrapper:

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

        self._initialize_handshake()
        self._slinda_workflow()

    def _slinda_workflow(self):
        # Broadcast a string
        broadcast = self._broadcast_str("Test Message: %s" % random.randint(10, 99))
        print(broadcast)

        # Broadcast a dictionary as an object
        broadcast = self._broadcast_obj({"OK %d" % random.randint(0, 9): "V %d" % random.randint(0, 9)})
        print(broadcast)

        # Broadcast entire files
        import requests
        img = requests.get("https://heiderlab.de/wordpress/wp-content/uploads/2019/10/Logo_HeiderLab.png", stream=True).raw.data
        submit = self._broadcast_raw(img)
        for s in submit.keys():
            with open("/home/roman/%s_picture_%d.png" % (self.args.host, s), "wb") as f:
                f.write(submit[s])
            f.close()

    def _broadcast(self, data, encode, decode) -> list:
        bucket: list = []
        bytes_coded_data: bytes = encode(data)
        answers = self._broadcast_raw(bytes_coded_data)
        for key in answers.keys():
            bucket.append(decode(answers[key]))
        return bucket

    def _broadcast_str(self, msg: str) -> list:
        return self._broadcast(msg, lambda e: str(e).encode("utf8"),
                        lambda d: bytes(d).decode("utf8"))

    def _broadcast_obj(self, obj: object) -> list:
        return self._broadcast(obj, lambda e: pickle.dumps(e), lambda d: pickle.loads(d))

    def _initialize_handshake(self):
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

    def _start_initialization_round(self):
        print("Starting server in a separate thread for handshaking")
        thread = Thread(target=self.run_server, args=(True,))
        thread.start()
        client = self.run_client(True)
        thread.join()
        if self.verbose >= 1:
            print("==> Handshake complete!")
        return client.keyring

    def _broadcast_raw(self, payload: bytes):
        if self.args.test is not None and self.args.test == "r2client":
            client = self.run_client()
            client.send_payload(payload)
            return None
        elif self.args.test is not None and self.args.test == "r2server":
            server = self.run_server()
            return server.get_answers()
        else:
            print("Starting server in a separate thread for broadcasting")
            results: dict = {}
            thread = Thread(target=self.run_server, args=(False, results))
            thread.start()
            client = self.run_client()
            client.send_payload(payload)
            thread.join()
            if self.verbose >= 1:
                print("==> Broadcasting finished")
            return results

    def run_server(self, initial: bool = False, results: dict = {}):
        """
        Loads the P2P Server class, that is listening.
        :return: the server class object
        """
        from lib.p2p_server import sLinDAserver
        server = sLinDAserver(self.args, self.keyring, initial, results)
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