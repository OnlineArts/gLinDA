from PyQt6 import QtCore

from gLinDA.lib.errors import LindaInternalError, GlindaP2PError
from gLinDA.lib.p2p import Runner
from gLinDA.lib.linda import LinDA


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
        self.progress.emit(0)
        #from linda import LinDA
        cfg: dict = self.config["LINDA"]
        linda = LinDA()
        results: dict = {}

        try:
            results = linda.run_local(cfg)
            self.progress.emit(1)

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
        Performs the P2P execution
        :return:
        """

        self.progress.emit(0)
        cfg: dict = self.config["LINDA"]
        linda = LinDA()
        results: str = ""

        try:
            params = linda.run_sl(self.config["LINDA"])

            self.progress.emit(1)
            p2p = Runner(self.config["P2P"])

            self.progress.emit(2)
            replies: dict = p2p.broadcast_obj(params)
            replies.update({0: params})

            results = linda.run_sl_avg(replies, cfg["formula"], not cfg["intersection"])

        except LindaInternalError as e:
            results: dict = {"ERROR": e}
            raise GlindaP2PError(e)
        finally:
            self.progress.emit(3)
            self.results.emit(results)
            self.finished.emit()