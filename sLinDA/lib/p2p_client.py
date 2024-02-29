from .p2p import sLinDAP2P

import random
import socket
from argparse import ArgumentParser


class sLinDAclient(sLinDAP2P):

    def __init__(self, args: ArgumentParser):
        super().__init__(args)
        peer = args.p[0]
        self.__test(peer)

    def __test(self, peer: str):
        host, port = peer.split(":")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                random_number = random.randint(super().min_rand,super().max_rand)
                msg = super().encrypt(random_number.to_bytes(3, "big"))
                if self.verbose >= 1:
                    print("Client: send random number %d" % random_number)
                s.connect((host, int(port)))
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
                print("Error: Connection refused by the peer")
                print("Are you sure the peer is reachable?")
            except Exception as e:
                print(e)
