#!/bin/env python3
import random
import pickle
from argparse import ArgumentParser
from threading import Thread

from sLinDA.lib.config import sLinDAConfig


class sLinDAWrapper:

    keyring: object = None

    def __init__(self, arguments: ArgumentParser):
        """
        Initialize the server and or client class
        :param arguments: All arguments
        """

        self.config = sLinDAConfig(arguments).get()
        self.verbose = self.config["P2P"]["verbose"]

        if self.verbose >= 1:
            print("Awaited clients: %d" % len(self.config["P2P"]["peers"]))

        if len(self.config["P2P"]["peers"]) == 1 and self.config["P2P"]["peers"][0] == self.config["P2P"]["host"]:
            print("Self-Test")

        self.__initialize_keyring()
        self._example_workflow()

    def _example_workflow(self):
        # Broadcast a string
        broadcast = self._broadcast_str("Test Message: %s" % random.randint(10, 99))
        print(broadcast)

        # Broadcast a dictionary as an object
        #broadcast = self._broadcast_obj({"OK %d" % random.randint(0, 9): "V %d" % random.randint(0, 9)})
        #print(broadcast)

        # Broadcast entire files
        """import requests
        img = requests.get("https://heiderlab.de/wordpress/wp-content/uploads/2019/10/Logo_HeiderLab.png", stream=True).raw.data
        submit = self._broadcast_raw(img)
        for s in submit.keys():
            with open("/home/roman/%s_picture_%d.png" % (self.config["P2P"]["host"], s), "wb") as f:
                f.write(submit[s])
            f.close()"""

    def _broadcast(self, data, encode: callable, decode: callable, as_list: bool = True) -> list:
        """
        Submits and receives all types of data. data will be encoded prior submission by the encode function and
        all participants datas will be decoded by the decode function.
        :param data: the data that will be broadcast.
        :param encode: a encoding function, should encode data and return byte arrays
        :param decode: a decoding function, decoding bytes into the desired data type
        :param as_list: if False participants data will be provided in dictionaries instead of a list
        :return:  or dictionary with the values from the other participants.
        """
        bucket = [] if as_list else {}
        bytes_coded_data: bytes = encode(data)
        reception = self._broadcast_raw(bytes_coded_data)

        for submitter in reception.keys():
            bucket.append(decode(reception[submitter])) if as_list else (
                bucket.update({submitter: decode(reception[submitter])}))

        return bucket

    def _broadcast_str(self, string: str) -> list:
        """
        Broadcast a string and receives a list of strings
        :param string: the massage submitted from this participant
        :return: a list of strings from the other participants
        """
        return self._broadcast(string, lambda e: str(e).encode("utf8"),
                               lambda d: bytes(d).decode("utf8"))

    def _broadcast_obj(self, object: object) -> list:
        """
        Broadcast an object and receives a list of objects
        :param object: the data object submitted from this participant
        :return: a list of objects from the other participants
        """
        return self._broadcast(object, lambda e: pickle.dumps(e), lambda d: pickle.loads(d), False)

    def _broadcast_raw(self, payload: bytes):
        if self.config["P2P"]["test"] is not None and self.config["P2P"]["test"] == "r2client":
            client = self.run_client()
            client.send_payload(payload)
            return None
        elif self.config["P2P"]["test"] is not None and self.config["P2P"]["test"] == "r2server":
            server = self.run_server()
            return server.get_answers()
        else:
            if self.verbose >= 1:
                print("sLinDA: Starting server in a separate thread for broadcasting")
            results: dict = {}
            thread = Thread(target=self.run_server, args=(False, results))
            thread.start()
            client = self.run_client()
            client.send_payload(payload)
            thread.join()
            if self.verbose >= 1:
                print("=> Broadcasting finished")
            return results

    def __initialize_keyring(self):
        """

        :return:
        """
        if self.config["P2P"]["test"] is not None and self.config["P2P"]["test"] == 'server':
            self.run_server()
        elif self.config["P2P"]["test"] is not None and self.config["P2P"]["test"] == 'client':
            self.run_client()
        else:
            keyring = self.__initialize_handshake()
            if len(keyring) != (2 * len(self.config["P2P"]["peers"])):
                print("Keyring incomplete, could not chat with every peer!")
                exit(101)
            elif self.verbose >= 2:
                print(keyring.get_peers())
            elif self.verbose >= 1:
                print("Keyring is complete!")
            self.keyring = keyring

    def __initialize_handshake(self):
        """
        Runs the multi-thread initialization, handshaking.
        :return: return a full keyring
        """
        print("Starting server in a separate thread for handshaking")
        thread = Thread(target=self.run_server, args=(True,))
        thread.start()
        client = self.run_client(True)
        thread.join()
        if self.verbose >= 1:
            print("==> Handshake complete!")
        return client.keyring

    def run_server(self, initial: bool = False, results: dict = {}):
        """
        Loads the P2P Server class, that is listening.
        :return: the server class object
        """
        from lib.p2p_server import sLinDAserver
        server = sLinDAserver(self.config, self.keyring, initial, results)
        return server

    def run_client(self, initial: bool = False):
        """
        Loads the P2P Client class, that submits data.
        :return: the client class object
        """
        from lib.p2p_client import sLinDAclient
        client = sLinDAclient(self.config, self.keyring, initial)
        return client


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
    sLinDAWrapper(args)


if __name__ == "__main__":
    main()