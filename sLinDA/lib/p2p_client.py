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
                random_number =  random.randint(100,999)
                msg = super().encrypt_text(text=str(random_number))
                if self.verbose >= 1:
                    print("Client: send random number %d" % random_number)
                s.connect((host, int(port)))
                s.sendall(msg)
                data = s.recv(1024)
                decrypted_answer = super().decrypt_text(data)

                if self.verbose >= 2:
                    print("Client: received data: %s" % str(data))
                    print("Client: decrypted message: %s" % decrypted_answer)

                if self.verbose >= 1:
                    if int(decrypted_answer) == (random_number+1):
                        print("Client: Encrypted communication was successful")

                s.close()
            except ConnectionRefusedError as e:
                print("Error: Connection refused by the peer")
                print("Are you sure the peer is reachable?")
            except Exception as e:
                print(e)
