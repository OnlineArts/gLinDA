import os
from subprocess import Popen, PIPE
from os import mkdir, path
from argparse import ArgumentParser
from multiprocessing import Process, Manager

class Benchmarker:

    def __init__(self, arguments: ArgumentParser):
        config_files = arguments.configs
        peers = [int(x) for x in arguments.peers]

        if not path.exists(arguments.output):
            mkdir(arguments.output)

        for config in config_files:
            config_name = self._get_filename(config)
            for peer in peers:
                print("Config: %s, Peers: %d" % (config_name, peer))
                results = self.test_loop(config, peer, arguments.output)
                with open("%s/%s_%d.txt" % (arguments.output, config_name, peer), "w" ) as file:
                    file.write(results)

    def test_loop(self, config_path: str, peers: int, output: str):
        if peers <= 1:
            return self.test_standalone(config_path, output=output, i=0, peers=1)
        else:
            return self.test_swarm_learning(config_path, peers, output)

    def test_swarm_learning(self, config: str, peers: int, output: str):
        returns = ""
        config_line: dict = ""

        if not path.exists(output+"/tmp"):
            mkdir(output+"/tmp")

        with Popen(["python", "dataset_splitter.py", "-config", config, "-peers", str(peers), "-output",
                    output+"/tmp"], stdout=PIPE) as proc:
            splits = proc.stdout.read().decode("utf8")
            lines = splits.split("\n")
            for l in lines:
                if l.find("Configs: [") != -1:
                    l1 = l[len("Configs: ["):-1].split(",")
                    config_line = [x.strip()[1:-1] for x in l1]
                    break

        if not len(config_line):
            return returns

        manager: Manager = Manager()
        bucket_list = manager.list()
        process_list: list = []
        for i in range(0, peers):
            process_list.append(Process(target=self.test_standalone, args=(config_line[i], bucket_list, output, i, peers)))

        [p.start() for p in process_list]
        [p.join() for p in process_list]

        returns = bucket_list[0]

        process_list: list = []
        for i in range(0, peers):
            process_list.append(Process(target=self.only_a_node, args=(config_line[i], [], output, i, peers)))
        [p.start() for p in process_list]
        [p.join() for p in process_list]

        return returns

    def test_standalone(self, config, bucket_list: list = [], output: str = "", i: int = 0, peers: int = 0):
        parameters = ["python", "glinda.py", "--config", config]
        dir = "%s_p%d" % (output, peers)
        try:
            if not os.path.exists(dir):
                os.mkdir(dir)
        except:
            pass
        if i == 0:
            parameters.extend(["--output", dir])
        with Popen(parameters, stdout=PIPE) as proc:
            results = proc.stdout.read().decode("utf8")
            bucket_list.append(results)
            return results

    def only_a_node(self, config, bucket_list: list = [], output: str = "", i: int = 0, peers: int = 1):
        dir = "%s_p%d_n%d" % (output, peers, i+1)
        if not os.path.exists(dir):
            os.mkdir(dir)
        parameters = ["python", "glinda.py", "--config", config, "--output", dir, "--standalone"]
        with Popen(parameters, stdout=PIPE) as proc:
            results = proc.stdout.read().decode("utf8")
            bucket_list.append(results)
            return results

    @staticmethod
    def _get_filename(path: str) -> str:
        if path.find("/") != -1:
            filename = path[path.rfind("/")+1:]
        elif path.find("\\") != -1:
            filename = path[path.rfind("\\")+1:]
        else:
            filename = path

        if filename.find(".") != -1:
            filename = filename[:filename.rfind(".")]

        return filename


def main():
    """
    Parses arguments
    """
    parser = ArgumentParser()
    parser.add_argument("-peers", nargs="+",
                        help="A list of numbers of peers to test")
    parser.add_argument("-configs", nargs="+",
                        help="A list of configuration files")
    parser.add_argument("--output", type=str, default="benchmark", help="directory to store all results")
    args = parser.parse_args()
    Benchmarker(args)

if __name__ == "__main__":
    main()