import configparser
import argparse
import os


class Config:
    """
    Conserves all configuration values
    (GUI) > Arguments > Configuration file
    """

    config: dict = {
        "P2P": {
            "host":         None,
            "peers":        [],
            "password":     None,
            "verbose":      0,
            "asymmetric":   True,
            "solo_mode":    False,
            "ignore_keys":  False,  # only for internal use
            "test":         None,   # only for internal use
            "resolve_host": True,   # only for internal use
        },
        "LINDA": {
            "formula":              "",
            "feature_table":        "",
            "metadata_table":       "",
            "feature_data_type":    "count",
            "prevalence":           0,
            "mean_abundance":       0,
            "max_abundance":        0,
            "zero_handling":        "pseudo_count",
            "p_adjustment_method":  "BH",
            "alpha":                0.05,
            "outlier_percentage":   0.03,
            "pseudo_count":         0.5,
            "correction_cutoff":    0.1,
            "verbose":              False,
            "winsor":               True,
            "adaptive":             True
        }
    }
    ip_filter: list = ["localhost", "127.0.0.1", "::1"]
    msg: str = ""

    def __init__(self, arguments: argparse.ArgumentParser = None, ini_path: str = None, check_sanity: bool = True):
        if arguments is None and ini_path is None:
            print("Use default configuration only")

        if arguments is not None:
            config_path = arguments.config
        elif ini_path is not None:
            config_path = ini_path
        else:
            config_path = None

        # Reading in arguments
        if config_path is not None and os.path.exists(config_path):
            configs = self._config_parser(config_path)
            self.config = self.merge_dictionary(self.config, configs)

        if arguments is not None:
            arg_filtered = self._argument_parser(arguments)
            self.config = self.merge_dictionary(self.config, arg_filtered)

        self.cast_parameters()
        if self.config["P2P"]["resolve_host"] and self.config["P2P"]["resolve_host"] is not None:
            self.__resolve_host(False)

        if self.config["P2P"]["verbose"] >= 1:
            print("Config #1: Initial configuration defined:")
            print(self.config)

        if check_sanity and not self.check_sanity():
            exit(110)

    def cast_parameters(self):
        """
        Check if important variables have the right type and cast them
        """
        if type(self.config["P2P"]["peers"]) is str:
            self.config["P2P"]["peers"] = self.config["P2P"]["peers"].split(" ")

        if type(self.config["P2P"]["verbose"]) is str:
            self.config["P2P"]["verbose"] = int(self.config["P2P"]["verbose"])

        self.config["P2P"]["ignore_keys"] = self._cast_bool(self.config["P2P"]["ignore_keys"])
        self.config["P2P"]["asymmetric"] = self._cast_bool(self.config["P2P"]["asymmetric"])
        self.config["P2P"]["solo_mode"] = self._cast_bool(self.config["P2P"]["solo_mode"])

        self.config["LINDA"]["winsor"] = self._cast_bool(self.config["LINDA"]["winsor"])
        self.config["LINDA"]["adaptive"] = self._cast_bool(self.config["LINDA"]["adaptive"])

    def __resolve_host(self, include_own_host: bool = False) -> bool:
        """
        Try to resolve a fitting host from all peers based on the own available own ip addresses.
        Overwrites the config if matching.
        :param include_own_host: should a defined host definition included?
        :return: True if a unique match occurred.
        """
        try:
            import socket
            all_ips = list(self.__get_ip_addresses(socket.AF_INET)) + list(self.__get_ip_addresses(socket.AF_INET6))
            ips = list(filter(lambda x: (x[1] not in self.ip_filter), all_ips))

            if self.config["P2P"]["verbose"] >= 2:
                print("Network interfaces detected: %s" % str(ips))

        except Exception as e:
            if self.config["P2P"]["verbose"] >= 1:
                print("Could not identify own ip address")
                print(e)
            return False

        if include_own_host:
            all_hosts: list = self.config["P2P"]["peers"] + self.config["P2P"]["host"]
        else:
            all_hosts: list = self.config["P2P"]["peers"]
        matches: list = []

        for host_port in all_hosts:
            host: str = host_port.split(":")[0]
            for ip in ips:
                if host == ip[1]:
                    matches.append(host)

        if len(matches) > 1:
            if self.config["P2P"]["verbose"] >= 2:
                print("Config #2: Ambiguous IP detection, stop IP resolution.")
        elif len(matches) == 0:
            if self.config["P2P"]["verbose"] >= 1:
                print("Config #1: No possible fitting host identified: %s in %s" %
                      ([h.split(":")[0] for h in all_hosts], [ip[1] for ip in ips]))
        elif len(matches) == 1:
            if self.config["P2P"]["verbose"] >= 1:
                print("Config #1: Identified %s as the host address" % matches[0])

            self.config["P2P"]["peers"]: list = []
            for peer in all_hosts:
                if peer.split(":")[0] != matches[0]:
                    self.config["P2P"]["peers"].append(peer)
                else:
                    self.config["P2P"]["host"] = peer

            return True
        return False

    def set(self, new_config: dict):
        """
        Overwrite the self.config dictionary.
        :param new_config: the new configuration
        """
        self.config = new_config

    def get(self) -> dict:
        """
        Return the final config
        :return: the config
        """
        return self.config

    def check_sanity(self):
        """
        Check if basic requirements are fulfilled
        """

        # LinDA configuration
        if "alpha" not in self.config["LINDA"] or not self.is_float(self.config["LINDA"]["alpha"]):
            self.msg = "Config: Alpha does not look like a floating number"
            print(self.msg)
            return False
        elif self.is_float(self.config["LINDA"]["alpha"]) and not (0 < float(self.config["LINDA"]["alpha"]) < 1):
            self.msg = "Config: Alpha should be bigger than 0 and smaller than 1"
            print(self.msg)
            return False

        if "outlier_percentage" not in self.config["LINDA"] or not self.is_float(self.config["LINDA"]["outlier_percentage"]):
            self.msg = "Config: outlier_percentage does not look like a floating number"
            print(self.msg)
            return False
        elif self.is_float(self.config["LINDA"]["outlier_percentage"]) and not (0 < float(self.config["LINDA"]["outlier_percentage"]) < 1):
            self.msg = "Config: outlier_percentage should be bigger than 0 and smaller than 1"
            print(self.msg)
            return False

        if not len(self.config["LINDA"]["feature_table"]) or not os.path.exists(self.config["LINDA"]["feature_table"]):
            self.msg = "Config: Feature Table data table does not exists"
            print(self.msg)
            return False

        if not len(self.config["LINDA"]["metadata_table"]) or not os.path.exists(self.config["LINDA"]["metadata_table"]):
            self.msg = "Config: Meta data table does not exists"
            print(self.msg)
            return False

        if not len(self.config["LINDA"]["formula"]):
            self.msg = "Config: Formula is missing"
            print(self.msg)
            return False

        # P2P configuration
        ## Solo Mode
        if self.config["P2P"]["solo_mode"] is not None and self.config["P2P"]["solo_mode"]:
            return True

        if self.config["P2P"]["password"] is None or len(self.config["P2P"]["password"]) == 0:
            self.msg = "Config: Can not run without a common password."
            print(self.msg)
            return False

        if "peers" not in self.config["P2P"] or self.config["P2P"]["peers"] is None or len(self.config["P2P"]["peers"]) == 0:
            self.msg = "Config: Missing peers. You can not run gLinDA only by yourself."
            print(self.msg)
            return False
        elif type(self.config["P2P"]["peers"]) is not list:
            self.msg = "Config: Expecting a list of peers"
            print(self.msg)
            return False
        else:
            for peer in self.config["P2P"]["peers"]:
                if not self._is_ip_and_port(peer):
                    return False

        if "host" not in self.config["P2P"] or self.config["P2P"]["host"] is None or len(self.config["P2P"]["host"]) == 0:
            print("Config: Missing host. You can not run gLinDA without finding or defining your own host address.")
            return False
        elif not self._is_ip_and_port(self.config["P2P"]["host"]):
            print("Config: Host is not correctly formatted, expected IP:Port")
            return False

        return True

    def save_config_to_file(self, path: str):
        lines: int = 0

        with open(path, "w") as f:
            for category in self.config.keys():
                spacer = "\r\n\r\n" if lines > 0 else ""
                f.write("%s[%s]" % (spacer, category))
                for key in self.config[category].keys():
                    value = self.config[category][key]
                    if type(value) is list:
                        value = " ".join(value)
                    f.write("\r\n%s = %s" % (key, str(value)))
                    lines += 1
        f.close()

    @staticmethod
    def is_float(value: str) -> bool:
        try:
            float(value)
            return True
        except ValueError:
            return False

    @staticmethod
    def _is_ip_and_port(value: str) -> bool:
        if ":" in value:
            ip = value[:value.rfind(":")]
            port = value[value.rfind(":")+1:]
            if len(ip) and len(port) and port.isnumeric():
                return True

        return False

    @staticmethod
    def _cast_bool(value):
        """
        Cast a (string) value (True, False, 1, 0) to a boolean
        :param value: the value
        :return: a boolean
        """
        if type(value) is not str:
            value = str(value)

        value = value.lower()
        return True if (value == "true" or value == "1" or value == "yes") else False

    @staticmethod
    def _cast_float(value):
        if Config.is_float(value):
            return float(value)
        else:
            return 0.0

    @staticmethod
    def _config_parser(config_file_path: str) -> dict:
        """
        Reads and converts the configparser object into a dictionary
        :param config_file_path: the path to the ini config file
        :return: dictionary
        """
        local_dictionary: dict = {}
        config = configparser.ConfigParser()
        config.read(config_file_path)

        for section in config.sections():
            items = config.items(section)
            local_dictionary[section] = dict(items)

        return local_dictionary

    @staticmethod
    def merge_dictionary(initial: dict, update: dict) -> dict:
        """
        Merging dictionaries, last one is dominating
        :param initial: first dictionary
        :param update: last and dominant dictionary
        :return:
        """
        return {
            "P2P": initial["P2P"] | update["P2P"],
            "LINDA": initial["LINDA"] | update["LINDA"]
        }

    @staticmethod
    def __get_ip_addresses(family) -> list:
        """
        Identify all available ip address
        :param family: the socket network family
        :return: list of interfaces and addresses
        """
        import psutil
        for interface, snics in psutil.net_if_addrs().items():
            for nic in snics:
                if nic.family == family:
                    yield (interface, nic.address)

    @staticmethod
    def _argument_parser(arguments: argparse.ArgumentParser):
        """
        Reads the arguments for the P2P network.
        :param arguments: the argument parser object
        :return: a filtered dictionary
        """
        dict_args: dict = vars(arguments)
        filter_args: dict = {}

        for name in dict_args.keys():
            value = dict_args[name]
            if value is not None:
                filter_args[name] = value

        return {"P2P": filter_args, "LINDA": {}}