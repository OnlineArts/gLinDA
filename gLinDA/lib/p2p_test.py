import random
from copy import deepcopy

from gLinDA.lib.config import Config
from gLinDA.lib.p2p import Runner


class P2PIsolationTester:

    def __init__(self, config: dict, test_case: str, max_loop: int = 100):
        self.config: dict = config
        self.test_case: str = test_case

        runner = Runner(self.config["P2P"])
        size_counter: int = 50
        loop_counter: int = 1
        testing: bool = True

        while testing and loop_counter <= max_loop:
            try:
                msg = P2PTester.get_dump_data(size_counter)
                send_data = runner.broadcast_obj(msg)
                print(send_data)
                size_counter += 25
                loop_counter += 1
            except KeyboardInterrupt:
                print("Closing at size %d, loop %d" % (size_counter, loop_counter))
                testing = False
            except Exception as e:
                print(e)
                testing = False

        exit(99)


class P2PTester:

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
        host_peers = P2PTester.host_permutator(P2PTester.host_generator(numbers))

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

    @staticmethod
    def get_dump_data(size) -> dict:
        msg: dict = {}
        for i in range(0, size):
            msg.update({"msg%d" % i: random.randint(1000, 9999)})
        return msg
