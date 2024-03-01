from .p2p import sLinDAP2P

import random
import socket
import time
from argparse import ArgumentParser


class sLinDAclient(sLinDAP2P):

    def __init__(self, args: ArgumentParser, keyring: object = None, initial: bool = False):
        super().__init__(args, keyring)

        if initial:
            if self.test is not None and self.test == "client":
                self.__initiate_communication(self.peers[0])
            else:
                for peer in self.peers:
                    self.__initiate_communication(peer)
                if self.verbose >= 1:
                    print("Client: I'm done!")

    def send_payload(self, raw_payload: bytes):
        for peer in self.peers:
            host, port = peer.split(":")
            not_connected = True
            chunk_nr: int = 0

            id, key = self.keyring.for_submission(peer)
            bid: bytes = int(id).to_bytes(self.bytes_len, "big")

            enc_payload = self.encrypt(raw_payload, key)
            msg: bytes = bid + enc_payload + "END:".encode("utf8") + bid

            print("Client: raw Massage: %s" % raw_payload.decode("utf8"))
            print("Client: target id %d, key %s" % (id, key))
            print("Client: byte identifier %s" % bid)
            print("Client: ciper %s" % enc_payload)
            print("Client: send %s" % msg)

            while not_connected:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    try:
                        s.connect((host, int(port)))
                        not_connected = False

                        if self.verbose >= 1:
                            print("Client: chunk data #%d" % chunk_nr)

                        s.sendall(msg)

                        s.close()
                    except ConnectionRefusedError as e:
                        print("Client: Are you sure the peer %s is reachable?" % peer)
                        print("Client: Retry connection in %d s" % super().waiting_time)
                        time.sleep(super().waiting_time)
                    except Exception as e:
                        print(e)

    def __initiate_communication(self, peer: str):
        host, port = peer.split(":")
        not_connected = True
        while not_connected:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.connect((host, int(port)))
                    not_connected = False
                    random_number = random.randint(super().min_rand, super().max_rand)
                    msg = super().encrypt(random_number.to_bytes(3, "big"))
                    if self.verbose >= 1:
                        print("Client: send random number %d" % random_number)

                    s.sendall(msg)

                    data = s.recv(self.chunk_size)
                    answer = super().decrypt(data)
                    confirmation_number = int.from_bytes(answer[:super().bytes_len], "big")

                    if confirmation_number != (random_number + 1):
                        s.close()
                        print("Client: Confirmation with %s failed, ignore peer" % peer)

                    else:
                        if self.verbose >= 1:
                            print("Client: Encrypted communication was successful")
                        self.keyring.add_peer(peer, (confirmation_number, answer[3:]), False)

                    s.close()
                except ConnectionRefusedError as e:
                    print("Client: Are you sure the peer %s is reachable?" % peer)
                    print("Client: Retry connection in %d s" % super().waiting_time)
                    time.sleep(super().waiting_time)
                except Exception as e:
                    print(e)