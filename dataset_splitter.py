import pandas
import numpy
import os

from copy import deepcopy
from argparse import ArgumentParser

from gLinDA.lib.config import Config
from gLinDA.lib.p2p_test import P2PTester


class DatasetSplitter:

    def __init__(self, arguments: ArgumentParser):
        if len(arguments.fraction):
            self.fractions = arguments.fraction
        else:
            self.fractions = [1.0/arguments.peers for i in range(arguments.peers)]

        self.linda_config: dict = Config(ini_path=arguments.config, check_sanity=False).get()["LINDA"]
        feature_table_path = self.linda_config["feature_table"]
        feature_index = self.linda_config["feature_index"]
        meta_table_path = self.linda_config["meta_table"]
        meta_index = self.linda_config["meta_index"]

        numpy.random.seed(arguments.seed)
        permutation, feature_paths = self._generate_split_datasets(feature_table_path, arguments.output, feature_index, True)
        permutation, meta_paths = self._generate_split_datasets(meta_table_path, arguments.output, meta_index, False, permutation)
        config_paths = self._generate_configs(arguments.config, feature_paths, meta_paths, arguments.output )

        print("Seed: %i, Splits: %i, Fractions: %s" % (arguments.seed, len(self.fractions), str(self.fractions)))
        print("Features: %s" % str(feature_paths))
        print("Meta: %s" % str(meta_paths))
        print("Configs: %s" % str(config_paths))

    def _generate_configs(self, config_path: str, feature_paths: list, meta_paths: list, output_path: str) -> list:
        config_paths: list = []
        configs = P2PTester.configuration_generator(len(self.fractions),
                                                    {"password": "Test", "asymmetric": False, "solo_mode": False}
                                                    )

        for i in range(0, len(self.fractions)):
            linda = deepcopy(self.linda_config)
            linda["feature_table"] = feature_paths[i]
            linda["meta_table"] = meta_paths[i]
            dummy_config = Config(check_sanity=False)
            dummy_config.set({"P2P": configs[i], "LINDA": linda})
            name = self._get_output_path(config_path, output_path, i + 1)
            dummy_config.save_config_to_file(name)
            config_paths.append(name)

        return config_paths

    @staticmethod
    def _get_fractions(raw_fractions: str) -> list:
        return [float(x) for x in raw_fractions.split(",")]

    @staticmethod
    def split(n, fractions):
        result = []
        for fraction in fractions[:-1]:
            result.append(round(fraction * n))
        result.append(n - numpy.sum(result))

        return result

    @staticmethod
    def _get_output_path(input_path: str, output_path: str, iteration: int):
        # linux path
        if input_path.find("/") != -1:
            filename = input_path[input_path.rfind("/")+1:]
        # windows path
        elif input_path.find("\\") != -1:
            filename = input_path[input_path.rfind("\\")+1:]
        else:
            filename = input_path

        extension = ""
        if filename.find(".") != -1:
            extension = filename[filename.rfind("."):]
            filename = filename[:filename.rfind(".")]

        if output_path[-1:] == "/" or output_path[-1:] == "\\":
            output_dir = output_path
        else:
            output_dir = output_path
            output_dir += "\\" if os.name == "nt" else "/"

        return output_dir + filename + "_" + str(iteration) + extension


    def _generate_split_datasets(self, dataset: str, output: str, index: str, feature: bool = False, permutation = None):
        data = pandas.read_csv(dataset, index_col=index)
        if feature:
            data = data.T
        m = data.shape[0]

        if permutation is None:
            permutation = numpy.random.permutation(m)

        shuffled_data = data.iloc[permutation]
        samples = self.split(m, self.fractions)
        arr = numpy.cumsum(samples)
        nodes_data = numpy.array_split(shuffled_data, arr)
        data_paths: list = []

        for i in range(0, len(self.fractions)):
            path = self._get_output_path(dataset, output, i+1)
            data_paths.append(path)
            ndata: pandas.DataFrame = nodes_data[i]
            if feature:
                ndata = ndata.T
            ndata.to_csv(path)

        return permutation, data_paths


def main():
    """
    Parses arguments
    """
    parser = ArgumentParser()
    parser.add_argument("-config", type=str, default="", help=
    "Provide configuration files with specific LINDA parameters for this dataset")
    parser.add_argument("-peers", type=int, default=2, help="Numbers of peers")
    parser.add_argument("-output", type=str, help="Path where to store the new data")
    parser.add_argument("--fraction", type=float, nargs='+', help="List of fraction sizes", default=[])
    parser.add_argument("--seed", type=int, default=42, help="Used seed for the split")
    args = parser.parse_args()
    DatasetSplitter(args)

if __name__ == "__main__":
    main()