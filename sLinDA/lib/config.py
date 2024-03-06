import configparser
import argparse

class sLinDAConfig:

    config: configparser.ConfigParser

    def __init__(self, passed_config: object):
        if type(passed_config) is str:
            self._config_parser(passed_config)
        elif type(passed_config) is argparse.ArgumentParser:
            self._argument_parser(passed_config)

    def _config_parser(self, config_file: str):
        config = configparser.ConfigParser()
        config.read(config_file)
        self.config = config

    def _argument_parser(self, arguments: argparse.ArgumentParser):
        print(arguments)
        self.config

    def get(self):
        return self.config