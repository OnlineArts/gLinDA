import timeout_decorator
import unittest
import sys
import random
from copy import deepcopy
from multiprocessing import Process, Manager

sys.path.insert(1, "../")

from gLinDA.lib.config import Config
from gLinDA.lib.p2p import Runner


class HelperFunctions:

    @staticmethod
    def expected_answers(replies: list, clients: int):
        count_answers: int = 0
        for an in replies:
            count_answers += len(an)

        return count_answers == (clients - 1) * clients

    @staticmethod
    def host_permutator(peers: list):
        bucket: list = []
        for host in peers:
            epeers = list(filter(lambda x: x != host, peers))
            bucket.append([host, epeers])
        return bucket

    @staticmethod
    def host_generator(number: int, hostname: str = "localhost", port_start: int = 5000):
        hosts: list = []
        port = port_start
        for i in range(0, number):
            hosts.append("%s:%d" % (hostname, port))
            port += 1
        return hosts

    @staticmethod
    def configuration_generator(numbers: int, general: dict = {}):
        basic_config: dict = Config(check_sanity=False).get()["P2P"]
        basic_config.update(general)
        configs: list = []
        host_peers = HelperFunctions.host_permutator(HelperFunctions.host_generator(numbers))

        for i in range (0, numbers):
            new_config = deepcopy(basic_config)
            new_config.update({"host": host_peers[i][0], "peers": host_peers[i][1]})
            configs.append(new_config)

        return configs

    @staticmethod
    def p2p_run(config: dict, bucket: list):
        p2p = Runner(config)
        broadcast = p2p.broadcast_str("Test Message #%s" % random.randint(1000, 9999))
        bucket.append(broadcast)


class SimulatePeers(unittest.TestCase):

    @timeout_decorator.timeout(300)
    def simulate_peers(self, peers: int, rsa: bool = False):
        general_param: dict = {"password": "Test", "verbose": 3}

        # Enable RSA
        if rsa:
            general_param.update({"asymmetric": True})
        else:
            general_param.update({"asymmetric": False})

        configs = HelperFunctions.configuration_generator(peers, general_param)
        manager: Manager = Manager()
        bucket_list = manager.list()
        process_list: list = []
        for i in range(0, peers):
            process_list.append(Process(target=HelperFunctions.p2p_run, args=(configs[i], bucket_list)))

        try:
            [p.start() for p in process_list]
            [p.join() for p in process_list]
        except timeout_decorator.TimeoutError as e:
            [p.kill() for p in process_list]

        return bucket_list

    def test_peer2peer_002n(self):
        self.assertTrue(HelperFunctions.expected_answers(self.simulate_peers(2), 2))

    def test_peer2peer_003n(self):
        self.assertTrue(HelperFunctions.expected_answers(self.simulate_peers(3), 3))

    def test_peer2peer_004n(self):
        self.assertTrue(HelperFunctions.expected_answers(self.simulate_peers(4), 4))

    def test_peer2peer_008n(self):
        self.assertTrue(HelperFunctions.expected_answers(self.simulate_peers(8), 8))

    def test_peer2peer_016n(self):
        self.assertTrue(HelperFunctions.expected_answers(self.simulate_peers(16), 16))

    def test_peer2peer_032n(self):
        self.assertTrue(HelperFunctions.expected_answers(self.simulate_peers(32), 32))

    def test_peer2peer_002n_rsa(self):
        self.assertTrue(HelperFunctions.expected_answers(self.simulate_peers(2, True), 2))

    def test_peer2peer_003n_rsa(self):
        self.assertTrue(HelperFunctions.expected_answers(self.simulate_peers(3, True), 3))

    def test_peer2peer_004n_rsa(self):
        self.assertTrue(HelperFunctions.expected_answers(self.simulate_peers(4, True), 4))

    def test_peer2peer_008n_rsa(self):
        self.assertTrue(HelperFunctions.expected_answers(self.simulate_peers(8, True), 8))
