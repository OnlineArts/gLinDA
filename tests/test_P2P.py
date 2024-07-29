import timeout_decorator
import unittest
import sys

from multiprocessing import Process, Manager

sys.path.insert(1, "../")


from gLinDA.lib.p2p_test import P2PTester


class SimulatePeers(unittest.TestCase):

    @timeout_decorator.timeout(300)
    def simulate_peers(self, peers: int, rsa: bool = False):
        general_param: dict = {"password": "Test", "verbose": 3}

        # Enable RSA
        if rsa:
            general_param.update({"asymmetric": True})
        else:
            general_param.update({"asymmetric": False})

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
