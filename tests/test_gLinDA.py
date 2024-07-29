import timeout_decorator
import unittest
import sys
from multiprocessing import Process, Manager
from argparse import ArgumentParser

sys.path.insert(1, "../")

from gLinDA.lib.config import Config
from gLinDA.lib.p2p import Runner
from gLinDA.lib.linda import LinDA
from glinda import Wrapper


class gLinDA_local_s5000(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        parser = ArgumentParser()
        parser.add_argument("--config", type=str)
        args = parser.parse_args(["--config", "../examples/s5000.ini"])
        wrapper = Wrapper(args, False)
        wrapper.config["LINDA"]["feature_table"] = "../%s" % wrapper.config["LINDA"]["feature_table"]
        wrapper.config["LINDA"]["meta_table"] = "../%s" % wrapper.config["LINDA"]["meta_table"]
        self.results = wrapper.run()["grp"]

    def test_local_s5000_complete(self):
        self.assertEqual(500, len(self.results), "The number of results is not complete")

    def test_local_s5000_reject_complete(self):
        res = self.results
        reject = res[res["reject"] == True]
        self.assertEqual(74, len(reject), "The number of rejected results is not complete")


class gLinDA_p2p_s5000_3peers(unittest.TestCase):

    @staticmethod
    def p2p_run(config: dict, bucket: list):
        coeffs = LinDA.run_sl(config["LINDA"])
        p2p = Runner(config["P2P"])
        replies = p2p.broadcast_obj(coeffs)
        replies.update({0: coeffs})
        results = LinDA.run_sl_avg(replies, config["LINDA"]["formula"])
        bucket.append(results)

    @timeout_decorator.timeout(300)
    def simulate_peers(self, peers: int):
        configs: list = []
        for i in range(1, peers+1):
            config = Config(None, "../examples/s5000_%d.ini" % i, check_sanity=False)
            config.get()["LINDA"]["feature_table"] = "../%s" % config.get()["LINDA"]["feature_table"]
            config.get()["LINDA"]["meta_table"] = "../%s" % config.get()["LINDA"]["meta_table"]
            configs.append(config.get())

        manager: Manager = Manager()
        bucket_list = manager.list()
        process_list: list = []
        for i in range(0, peers):
            process_list.append(Process(target=gLinDA_p2p_s5000_3peers.p2p_run, args=(configs[i], bucket_list)))

        try:
            [p.start() for p in process_list]
            [p.join() for p in process_list]
        except timeout_decorator.TimeoutError as e:
            [p.kill() for p in process_list]
        return bucket_list

    def test_complete(self):
        answers = self.simulate_peers(3, False)

        multi_check: list = [0 if len(answers) == 3 else 1, 0 if "grp" in answers[0] else 1,
                             0 if len(answers[0]["grp"]) == 500 else 1]

        self.assertFalse(bool(sum(multi_check)))
