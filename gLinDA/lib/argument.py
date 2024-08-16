from argparse import ArgumentParser

class Arguments:

    def __init__(self):
        parser = ArgumentParser()
        parser.add_argument("--host", help="The own host address and port")
        parser.add_argument("-pw", "--password", type=str, help="Mandatory password for communication")
        parser.add_argument("-p", "--peers", nargs="+",
                            help="A list with peer addresses and ports, e.g. localhost:5000 localhost:5001")
        parser.add_argument("-t", "--test", type=str, default=None, help="Developers")
        parser.add_argument('-v', '--verbose', action='count',
                            help="Enables verbose mode, repeat v for a higher verbose mode level")
        parser.add_argument("--ignore-keys", default=False, action='store_true',
                            help="Ignores wrong keys. Will not stop execution if wrong password communication are appearing")
        parser.add_argument("--config", type=str, help="path to config file")

        self.__args = parser.parse_args()

    def get_args(self):
        return self.__args