import random
import socket
import time

from gLinDA.lib.p2p import P2P, Keyring
from gLinDA.lib.p2p_pkg import P2PCollector, P2PPackage


class Client(P2P):

    def __init__(self, config: dict, keyring: Keyring = None, initial: bool = False):
        if keyring is None:
            keyring = Keyring()
        super().__init__(config, keyring)

        if initial:
            for peer in self.peers:
                print(peer)
                self.__initiate_communication(peer)
            if self.verbose >= 1:
                print("Client #1: I'm done!")

    def send_payload(self, raw_payload: bytes):
        for peer in self.peers:
            host, port = peer.split(":")
            pkg_counter: int = 1
            not_connected = True
            identifier, encrypt_key = self.keyring.for_submission(peer)

            if not self.config["asymmetric"]:
                self.encryption.set_init_vector(self.keyring.get_iv())

            enc_payload = self.encryption.encrypt(raw_payload, encrypt_key)
            p2p_pkgs: list = P2PPackage.build_packages(self.bytes_len, self.chunk_size, identifier,
                                                 enc_payload, self.verbose)

            if self.verbose >= 3:
                print("Client #3: Sending %d packages to %d" % (len(p2p_pkgs), identifier))
                print("Client #3: Packages %s" % str(p2p_pkgs))
                #print("Client #3: raw massage: %s" % raw_payload)
                print("Client #3: target id %d, key %s" % (identifier, encrypt_key))
                #print("Client #3: ciper (%d) %s" % (len(enc_payload), enc_payload))
            elif self.verbose >= 2:
                print("Client #2: Packages %s" % p2p_pkgs)
            elif self.verbose >= 1:
                print("Client #1: Send msg to %s:%d" % (host, int(port)))

            for n in p2p_pkgs:
                n: P2PPackage = n
                not_connected = True
                while not_connected:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        try:
                            s.connect((host, int(port)))
                            not_connected = False

                            binary_pkg = n.build_binary_package()

                            if self.verbose >= 3:
                                print("Client #3: Sending package #%d package: %s" % (pkg_counter, n))

                            s.sendall(binary_pkg)
                            s.close()

                        except ConnectionRefusedError as e:
                            if self.verbose >= 1:
                                print("Client #1: Are you sure the peer %s is reachable? Retry in %d s" %
                                      (peer, super().waiting_time))
                            time.sleep(super().waiting_time)
                            super().set_waiting_time(super().waiting_time + 1)
                        except Exception as e:
                            print(e)

                pkg_counter += 1
                time.sleep(super().waiting_time)

        time.sleep(super().waiting_time)  # Test, wait after sending

    def __initiate_communication(self, peer: str):
        try:
            host, port = peer.split(":")
            not_connected = True
            while not_connected:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    try:
                        s.connect((host, int(port)))
                        not_connected = False
                        random_number = random.randint(super().min_rand, super().max_rand)

                        msg = random_number.to_bytes(3, "big")
                        if self.config["asymmetric"]:
                            msg += self.keyring.get_keys(False)[1]  # public key

                        init_aes_key = self.get_init_key()
                        enc_msg = self.encryption.encrypt(
                            msg,
                            init_aes_key
                        )

                        if self.verbose >= 1:
                            print("ClientHandshake #1: Send random number %d to %s:%s" % (random_number, host, port))
                        if self.verbose >= 2:
                            print("ClientHandshake #2: Send raw msg %s" % enc_msg)

                        s.sendall(enc_msg)
                        data = s.recv(self.chunk_size)

                        if self.verbose >= 2:
                            print("ClientHandshake #2: Received answer encrypted %s" % data )
                            print("ClientHandshake #2: Will use decryption key %s" % init_aes_key )

                        answer = self.encryption.decrypt(
                            data,
                            init_aes_key
                        )

                        confirmation_number = int.from_bytes(answer[:super().bytes_len], "big")

                        if confirmation_number != (random_number + 1):
                            s.close()
                            print("Client #1: Confirmation with %s failed, ignore peer" % peer)

                        else:
                            if self.verbose >= 1:
                                print("Client #1: Encrypted communication was successful")
                            self.keyring.add_peer(peer, (confirmation_number, answer[self.bytes_len:]),
                                                  False)

                        s.close()
                    except ConnectionRefusedError as e:
                        if self.verbose >= 1:
                            print("Client #1: Are you sure the peer %s is reachable? Retry in %d s" % (
                                peer, super().waiting_time))
                        time.sleep(super().waiting_time)
                        super().set_waiting_time(super().waiting_time + 1)
                    except Exception as e:
                        print(e)

        except KeyboardInterrupt as e:
            print("Client #1: Terminated manually")
        time.sleep(super().waiting_time)  # Test, wait after sending
