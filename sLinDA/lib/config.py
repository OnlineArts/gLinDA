import configparser
import argparse
import os


class sLinDAConfig:

    config: dict = {
        "P2P": {
            "host":         None,
            "peers":        [],
            "password":     None,
            "verbose":      0,
            "test":         None,
            "ignore_keys":  False,
            "resolve_host": True
        },
        "LINDA": {
            "covariants":   None
        }
    }
    ip_filter: list = ["localhost", "127.0.0.1", "::1"]

    def __init__(self, arguments: argparse.ArgumentParser):
        config_path = arguments.config

        # Reading in arguments
        if config_path is not None and os.path.exists(config_path):
            configs = self._config_parser(config_path)
            self.config = self.merge_dictionary(self.config, configs)

        arg_filtered = self._argument_parser(arguments)
        self.config = self.merge_dictionary(self.config, arg_filtered)

        self.cast_parameters()
        if self.config["P2P"]["resolve_host"] and self.config["P2P"]["resolve_host"] is None:
            self.__resolve_host(False)

        if self.config["P2P"]["verbose"] >= 1:
            print("Config #1: Initial configuration defined:")
            print(self.config)

    def cast_parameters(self):
        """
        Check if important variables have the right type and cast them
        """
        if type(self.config["P2P"]["peers"]) is str:
            self.config["P2P"]["peers"] = self.config["P2P"]["peers"].split(" ")

        if type(self.config["P2P"]["verbose"]) is str:
            self.config["P2P"]["verbose"] = int(self.config["P2P"]["verbose"])

        if (type(self.config["P2P"]["ignore_keys"]) is str and self.config["P2P"]["ignore_keys"] == "True" or
                self.config["P2P"]["ignore_keys"] == "False"):
            self.config["P2P"]["ignore_keys"] = True if self.config["P2P"]["ignore_keys"] == "True" else False
            self.config["P2P"]["ignore_keys"] = True if self.config["P2P"]["ignore_keys"] == "1" else False

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
        except Exception as e:
            if self.config["P2P"]["verbose"] >= 1:
                print("Could not identify own ip address")
                print(e)
            return False

        all_hosts: list = self.config["P2P"]["peers"] + self.config["P2P"]["host"] if include_own_host else self.config["P2P"]["peers"]
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
                print("Config #1: No possible fitting host identified: %s in %s" % ([h.split(":")[0] for h in all_hosts], [ip[1] for ip in ips]))
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
        for int, snics in psutil.net_if_addrs().items():
            for nic in snics:
                if nic.family == family:
                    yield (int, nic.address)

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