from argparse import ArgumentParser

class Arguments:
    """
    In order to function with the same arguments for the CLI and GUI version, the argument handling is localized here.
    """

    def __init__(self):
        """
        Initializes the argument parser and stores them into a private dictionary.
        """
        parser = ArgumentParser()
        parser.add_argument("--host", help="The own host address and port")
        parser.add_argument("-pw", "--password", type=str, help="Mandatory password for communication")
        parser.add_argument("-p", "--peers", nargs="+",
                            help="A list with peer addresses and ports, e.g. localhost:5000 localhost:5001")
        parser.add_argument("-t", "--test", type=str, default=None, help="Developers")
        parser.add_argument('-v', '--verbose', action='count',
                            help="Enables verbose mode, repeat v for a higher verbose level")
        parser.add_argument("--ignore-keys", default=False, action='store_true',
                            help="Ignores wrong keys. Will not stop execution if wrong password communication are appearing")
        parser.add_argument("--intersection", default=False, action='store_true',
                            help="Use only intersection of commonly existing features instead the union")
        parser.add_argument("--config", type=str, help="path to config file")

        self.__args = parser.parse_args()

    def get_args(self):
        """
        Returns the parsed arguments.
        :return: the arguments.
        """
        return self.__args