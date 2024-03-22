from errors import LindaInternalError, GlindaP2PError
from p2p import Runner
from PyQt6 import QtCore


class gLinDALocalWorker(QtCore.QObject):
    """
    This object will run in a separate thread, containing the actual gLinDA execution
    """

    # These are Signals that communicate with the main GUI object thread
    finished = QtCore.pyqtSignal()
    progress = QtCore.pyqtSignal(int)
    results = QtCore.pyqtSignal(object)

    def set_config(self, config: dict):
        """
        Sets the configuration
        :param config: a dictionary with all configurations
        """
        self.config = config

    def run(self):
        from linda import LinDA
        cfg: dict = self.config["LINDA"]
        self.progress.emit(0)
        linda = LinDA()
        results: dict = {}

        try:
            results = linda.run(
                LinDA.read_table(cfg["feature_table"]),
                LinDA.read_table(cfg["metadata_table"]),
                cfg["formula"],
                cfg["feature_data_type"],
                "name",
                cfg["prevalence"],
                cfg["mean_abundance"],
                cfg["max_abundance"],
                cfg["winsor"],
                cfg["outlier_percentage"],
                cfg["adaptive"],
                cfg["zero_handling"],
                cfg["pseudo_count"],
                cfg["correction_cutoff"],
                cfg["verbose"]
            )
        except LindaInternalError as e:
            results: dict = {"ERROR": e}
            raise GlindaP2PError(e)
        finally:
            self.progress.emit(2)
            self.results.emit(results)
            self.finished.emit()


class gLinDAP2PWorker(QtCore.QObject):
    """
    This object will run in a separate thread, containing the actual gLinDA execution
    """

    # These are Signals that communicate with the main GUI object thread
    finished = QtCore.pyqtSignal()
    progress = QtCore.pyqtSignal(int)
    results = QtCore.pyqtSignal(object)

    def set_config(self, config: dict):
        """
        Sets the configuration
        :param config: a dictionary with all configurations
        """
        self.config = config

    def run(self):
        """
        Performs the P2P demo execution
        :return:
        """
        import random

        p2p = Runner(self.config["P2P"])
        self.progress.emit(0)
        strings = p2p.broadcast_str("Test Message: %s" % random.randint(10, 99))
        print(strings)
        self.progress.emit(1)
        my_msg = {"A %d" % random.randint(0, 9): "B %d" % random.randint(0, 9)}
        dicts = p2p.broadcast_obj(my_msg)
        self.progress.emit(2)
        self.results.emit("Own message: %s, received: %s" % (my_msg, dicts))
        self.finished.emit()