import unittest
import sys

sys.path.insert(1, "../")

from gLinDA.lib.config import Config
from gLinDA.lib.linda import LinDA


class LinDA_s5000(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        config = Config(None, "../examples/s5000.ini", check_sanity=False)
        config.get()["LINDA"]["feature_table"] = "../%s" % config.get()["LINDA"]["feature_table"]
        config.get()["LINDA"]["meta_table"] = "../%s" % config.get()["LINDA"]["meta_table"]
        results = LinDA.run_local(config.get()["LINDA"])
        self.results = results["grp"]

    def test_s5000_complete(self):
        self.assertEqual(500, len(self.results), "The number of results is not complete")

    def test_s5000_reject_complete(self):
        res = self.results
        reject = res[res["reject"] == True]
        self.assertEqual(74, len(reject), "The number of rejected results is not complete")

