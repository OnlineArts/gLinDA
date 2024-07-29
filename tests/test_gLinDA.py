import argparse
import unittest
import sys
from argparse import ArgumentParser

sys.path.insert(1, "../")

from gLinDA.lib.config import Config
from glinda import Wrapper


class gLinDA_local_s5000(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        parser = argparse.ArgumentParser()
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
    pass