from math import ceil
from pickle import dumps, loads


class P2PPackage:

    __payload: bytes = 0
    __identifier: int = 0
    __number: int = 0
    __stop: bool = False
    __bytes_length: int = 3
    verbose: int = 0

    def __init__(self, identifier_length: int = 3, verbose: int = 0):
        self.__bytes_length = identifier_length
        self.verbose = verbose

    @staticmethod
    def _get_identifier(data: bytes, verbose: int = 0, number: bool = False) -> int:
        name = "sequential number" if number else "identifier"

        if verbose >= 3:
            print("P2PPackage #3: potential binary %s %s" % (name, data))

        try:
            nr = int.from_bytes(data, "big")
        except TypeError:
            return 0

        if verbose >= 2:
            print("P2PPackage #2: %s %d" % (name, nr))

        return nr

    @staticmethod
    def _get_break(potential_brake: bytes, verbose: int = 0) -> bool:
        end = None

        if verbose >= 3:
            print("P2PPackage #3: potential end %s" % potential_brake)

        try:
            end = potential_brake.decode("utf8")

            if verbose >= 3:
                print("P2PPackage #3: end '%s'" % end)

        except UnicodeDecodeError as e:
            #print(e)
            return False
        except Exception as e:
            print(e)
            return False

        return end is not None and end == "END:"

    @staticmethod
    def build_packages(bytes_length: int, chunk_size: int, identifier: int, payload: bytes, verbose: int = 0):
        total_length: int = len(payload) - (bytes_length * 3 + 4)
        chunk_size_wo_header = chunk_size - ((bytes_length * 3) + 4)

        packages: int = ceil(total_length / chunk_size_wo_header)
        buckets: list = []

        for i in range(1, packages + 1):
            start_pos = (i - 1) * chunk_size_wo_header
            end_pos = i * chunk_size_wo_header
            entry: bytes = payload[start_pos:end_pos]

            new_pkg = P2PPackage(bytes_length, 0)
            new_pkg.set_identifier(identifier)
            new_pkg.set_number(i)
            new_pkg.set_payload(entry)
            new_pkg.set_stop(i == packages)

            buckets.append(new_pkg)

        return buckets

    def load(self, raw_data: bytes) -> bool:

        # Detect the identifier
        self.__identifier = self._get_identifier(raw_data[:self.__bytes_length], self.verbose)
        if self.__identifier == 0:
            return False

        # Check if complete
        end_id = self._get_identifier(raw_data[-self.__bytes_length:], self.verbose)
        if end_id == 0 or self.__identifier != end_id:
            print("P2PCollector: Incomplete package")
            return False

        # Detect the sequential number
        self.__number = self._get_identifier(raw_data[self.__bytes_length:(self.__bytes_length * 2)], self.verbose, True)

        # Detect a potential break
        payload: bytes = raw_data[self.__bytes_length*2:-self.__bytes_length]

        self.__stop = self._get_break(payload[-4:], self.verbose)

        if self.__stop:
            self.__payload = payload[:-4]
        else:
            self.__payload = payload

        return True

    def get_payload(self) -> bytes:
        return self.__payload

    def get_identifier(self) -> int:
        return self.__identifier

    def get_number(self) -> int:
        return self.__number

    def get_stop(self) -> bool:
        return self.__stop

    def set_stop(self, stop: bool):
        self.__stop = stop

    def set_payload(self, payload: bytes):
        self.__payload = payload

    def set_identifier(self, ident: int):
        self.__identifier = ident

    def set_number(self, nr: int):
        self.__number = nr

    def get_total_size(self) -> int:
        size = len(self) + 3 * self.__bytes_length  # 1x identifier, 1x number, 1x identifier
        if self.__stop:
            size += 4  # "END:"
        return size

    def build_binary_package(self) -> bytes:
        raw: bytes = self.__identifier.to_bytes(self.__bytes_length, "big")
        raw += self.__number.to_bytes(self.__bytes_length, "big")
        raw += self.__payload
        if self.__stop:
            raw += "END:".encode("utf8")
        raw += self.__identifier.to_bytes(self.__bytes_length, "big")
        return raw

    def __repr__(self) -> str:
        return ("P2PPackage (%d): Id: %d; Nr: %d; Last: %d; Payload (%d): %s" %
                (self.get_total_size(), self.__identifier, self.__number, int(self.__stop), len(self),
                 str(self.__payload)[:10]+"..."+str(self.__payload)[-10:] if len(self.__payload) else "--EMPTY--"))

    def __len__(self) -> int:
        return len(self.__payload)


class P2PCollector:

    def __init__(self, identifier_length: int = 3, verbose: int = 0, expected_peers: int = 0):
        self.identifiers: dict = {}
        self.payloads: dict = {}
        self.states: dict = {}
        self.bytes_length = identifier_length
        self.expected_peers = expected_peers
        self.verbose = verbose

    def load(self, packages):

        if not len(packages):
            return False

        if type(packages) is not list:
            packages = [packages]

        for pkg in packages:
            pkg: P2PPackage = pkg

            # damaged package?
            id = pkg.get_identifier()
            if id == 0:
                print("Package without an identifier: %s" % pkg)
                continue

            # new package
            if id not in self.identifiers:
                self.identifiers.update({id: True})
                self.states.update({id: pkg.get_stop()})
                self.payloads.update({id: [pkg]})
            else:
                self.payloads[id].append(pkg)
                if pkg.get_stop():
                    self.states.update({id: True})

    def get_payload(self, identifier: int) -> bytes:
        try:
            if not self.states[identifier]:
                print("It looks like this peers does not sent all his messages yet")

            sorted_payloads = sorted(self.payloads[identifier], key=lambda pay: pay.get_number())
            return b''.join([x.get_payload() for x in sorted_payloads])

        except KeyError:
            print("Can not find any payload for requested peer %d" % identifier)
            return b''

    def is_finished(self):
        completed = sum(self.states.values())
        if self.expected_peers:
            return completed == self.expected_peers

        return completed == len(self.identifiers)

    def __repr__(self) -> str:
        return "P2PCollector (%d) contains %d single packages from %d peers, of which %d are terminated." % (
            int(self.is_finished()), sum([len(x) for x in self.payloads.values()]), len(self.identifiers), sum(self.states.values())
        )