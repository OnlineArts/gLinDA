from .p2p import sLinDAP2P

import random
import socket
import time
from argparse import ArgumentParser


class sLinDAclient(sLinDAP2P):

    def __init__(self, args: ArgumentParser, keyring: object = None):
        super().__init__(args, keyring)

        if self.test != None:
            self.__initiate_communication(self.peers[0])
        else:
            for peer in self.peers:
                self.__initiate_communication(peer)

        if self.verbose >= 1:
            print("Client: I'm done!")

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

                    data = s.recv(1024)
                    answer = super().decrypt(data)
                    confirmation_number = int.from_bytes(answer[:super().bytes_len], "big")

                    if confirmation_number != (random_number + 1):
                        s.close()
                        print("Client: Confirmation with %s failed, ignore peer" % peer)

                    else:
                        if self.verbose >= 1:
                            print("Client: Encrypted communication was successful")
                        self.keyring.add_peer(peer, answer[3:], False)

                    s.close()
                except ConnectionRefusedError as e:
                    print("Client: Error: Connection refused by the peer")
                    print("Client: Are you sure the peer %s is reachable?" % peer)
                    print("Client: Retry connection in %d s" % super().waiting_time)
                    time.sleep(super().waiting_time)
                except Exception as e:
                    print(e)