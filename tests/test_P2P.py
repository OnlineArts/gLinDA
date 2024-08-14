import timeout_decorator
import unittest
import sys

from multiprocessing import Process, Manager
from pickle import dumps, loads
from random import randint

sys.path.insert(1, "../")

from gLinDA.lib.p2p import P2P, Runner, EncryptionAsymmetric, EncryptionSymmetric, Keyring
from gLinDA.lib.p2p_pkg import P2PPackage, P2PCollector
from gLinDA.lib.p2p_test import P2PTester


class SimulatePeers(unittest.TestCase):

    @timeout_decorator.timeout(300)
    def simulate_peers(self, peers: int, rsa: bool = False):
        general_param: dict = {"password": "Test", "verbose": 3, "asymmetric": rsa}
        configs = P2PTester.configuration_generator(peers, general_param)
        manager: Manager = Manager()
        bucket_list = manager.list()
        process_list: list = []
        for i in range(0, peers):
            process_list.append(Process(target=P2PTester.p2p_run, args=(configs[i], bucket_list)))

        try:
            [p.start() for p in process_list]
            [p.join() for p in process_list]
        except timeout_decorator.TimeoutError as e:
            [p.kill() for p in process_list]

        return bucket_list

    def test_manual_build_single_package(self):
        """
        Test whether binaries were correctly loaded.
        :return:
        """
        blen: int = 3
        full_package: bytes = (int(9199).to_bytes(blen, "big") + int(1).to_bytes(blen, "big")
                               + "Hello World!".encode("utf8") + "END:".encode("utf8")
                               + int(9199).to_bytes(blen, "big"))
        full_pkg = P2PPackage(blen, 0)
        full_pkg.load(full_package)
        self.assertEqual(full_pkg.get_payload().decode("utf8"), "Hello World!", "Single P2PPackage payload is wrong")

    def test_manual_build_multi_packages(self):
        """
        Test whether binaries can be split and reassembled correctly.
        :return:
        """
        blen: int = 3
        ident = 45423
        partial_package_1: bytes = (int(ident).to_bytes(blen, "big") + int(1).to_bytes(blen, "big")
                                    + "Hello".encode("utf8") + int(ident).to_bytes(blen, "big"))
        partial_package_2: bytes = (int(ident).to_bytes(blen, "big") + int(2).to_bytes(blen, "big")
                                    + " World!".encode("utf8") + "END:".encode("utf8")
                                    + int(ident).to_bytes(blen, "big"))
        pkg1 = P2PPackage(blen, 2)
        pkg1.load(partial_package_1)
        pkg2 = P2PPackage(blen, 2)
        pkg2.load(partial_package_2)

        collector = P2PCollector(blen, blen, 1)
        collector.load([pkg2, pkg1])

        self.assertEqual(collector.get_payload(ident).decode("utf8"),
                         "Hello World!", "The combined packages are not matching")

    def test_build_and_read(self):
        raw_bucket: dict = {randint(100,499): b'', randint(500, 999): b''}
        pkg_bucket: dict = {}

        for key in raw_bucket.keys():
            raw_bucket[key] = dumps(P2PTester.get_dump_data(200))
            pkg_bucket[key] = P2PPackage.build_packages(3, 1024, key, raw_bucket[key], 2)

        collection = P2PCollector(3, 3, 2)
        for item in pkg_bucket.values():
            collection.load(item)

        # compare each entry
        similar = True
        for key, item in raw_bucket.items():
            if item != collection.get_payload(key):
                similar = False
                break

        self.assertTrue(similar, "After creating and reassembling packages, the bytes differs")

    def test_build_and_read_encrypted_packages(self):
        preliminary_cfg = {"password": "T35T", "verbose": 3, "asymmetric": False}
        config = P2PTester.configuration_generator(2, preliminary_cfg)[0]

        keyring = Keyring()
        p2p = P2P(config, keyring)
        self.enc: EncryptionSymmetric = EncryptionSymmetric(config)
        self.enc.set_init_vector(keyring.get_iv())

        raw_bucket: dict = {randint(100,499): b'', randint(500, 999): b''}
        pkg_bucket: dict = {}

        for key in raw_bucket.keys():
            keyring.add_peer(str(key), (key, p2p.get_init_key()), False)
            identifier, aes_key = keyring.for_submission(str(key))
            data = P2PTester.get_dump_data(200)
            raw_bucket[key] = data
            pkg_bucket[key] = P2PPackage.build_packages(3, 1024, key, self.enc.encrypt(dumps(data), aes_key), 2)

        collection = P2PCollector(3, 3, 2)
        for item in pkg_bucket.values():
            collection.load(item)

        # compare each entry
        similar = True
        for key, item in raw_bucket.items():
            identifier, aes_key = keyring.for_submission(str(key))
            msg = loads(self.enc.decrypt(collection.get_payload(key), aes_key))
            if item != msg:
                similar = False
                break

        self.assertTrue(similar, "After creating, encrypting and reassembling packages, the bytes differs")

    def test_peer2peer_002n(self):
        self.assertTrue(P2PTester.expected_answers(self.simulate_peers(2), 2))

    def test_peer2peer_003n(self):
        self.assertTrue(P2PTester.expected_answers(self.simulate_peers(3), 3))

    def test_peer2peer_004n(self):
        self.assertTrue(P2PTester.expected_answers(self.simulate_peers(4), 4))

    def test_peer2peer_008n(self):
        self.assertTrue(P2PTester.expected_answers(self.simulate_peers(8), 8))

    def test_peer2peer_016n(self):
        self.assertTrue(P2PTester.expected_answers(self.simulate_peers(16), 16))

    def test_peer2peer_032n(self):
        self.assertTrue(P2PTester.expected_answers(self.simulate_peers(32), 32))

    def test_peer2peer_002n_rsa(self):
        self.assertTrue(P2PTester.expected_answers(self.simulate_peers(2, True), 2))

    def test_peer2peer_003n_rsa(self):
        self.assertTrue(P2PTester.expected_answers(self.simulate_peers(3, True), 3))

    def test_peer2peer_004n_rsa(self):
        self.assertTrue(P2PTester.expected_answers(self.simulate_peers(4, True), 4))

    def test_peer2peer_008n_rsa(self):
        self.assertTrue(P2PTester.expected_answers(self.simulate_peers(8, True), 8))
