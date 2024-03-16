import time

from config import Config
from p2p import Runner
from PyQt6 import QtWidgets, QtCore, uic, QtGui

import sys


class MainWindow(QtWidgets.QMainWindow):

    peer_fields: int = 4

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi("gui.ui", self)
        self.setWindowIcon(QtGui.QIcon("logo.png"))

        # gLinDA Configuration
        self.config: Config = Config(check_sanity=False)
        self._default_startup()

    def _default_startup(self):
        # Basic layout
        self.Tabs: QtWidgets.QTabWidget = self.TabWidget

        # Menu bar
        self.Open: QtWidgets.QWidgetAction = self.actionOpenConfig
        self.Save: QtWidgets.QWidgetAction = self.actionSaveConfig
        self.Export: QtWidgets.QWidgetAction = self.actionExportConfig

        # Configuration tab
        self.host_field: QtWidgets.QLineEdit = self.HostInput
        self.password_field: QtWidgets.QLineEdit = self.PasswordInput
        self.covariant: QtWidgets.QLineEdit = self.CovariantInput

        # Results tab
        self.ResultText: QtWidgets.QTextBrowser = self.ResultLabel

        # Footer
        self.Message: QtWidgets.QLabel = self.MessageLabel
        self.Progress: QtWidgets.QProgressBar = self.ProgressBar
        self.Run: QtWidgets.QPushButton = self.RunButton

        # Default values
        self.Message.setText("")
        self.Progress.hide()
        self.Run.setEnabled(False)
        self.Tabs.setTabVisible(1, False)  # Index 1: Results
        self.Save.setEnabled(False)
        self.Export.setEnabled(False)

    def load_configuration_file(self):
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Open a gLinDA configuration file", "", "Configuration ini file (*.ini *.INI)")
        if filename:
            self.__import_config_file(filename)

    def __import_config_file(self, config_path: str):
        self.config: Config = Config(ini_path=config_path, check_sanity=False)
        config = self.config.get()

        # host
        if config["P2P"]["host"] is not None and len(config["P2P"]["host"]):
            self.host_field.setText(config["P2P"]["host"])

        # password
        if config["P2P"]["password"] is not None and len(config["P2P"]["password"]):
            self.password_field.setText(config["P2P"]["password"])

        if config["P2P"]["peers"] is not None and type(config["P2P"]["peers"]) is list and \
            len(config["P2P"]["peers"]):
            for i in range(0, len(config["P2P"]["peers"])):
                if i > self.peer_fields:
                    break
                peer_i: QtWidgets.QLineEdit = self.__getattribute__("Peer%dInput" % (i+1))
                peer_i.setText(config["P2P"]["peers"][i])

        self.check_run_btn()

    def save_config(self):
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Store configuration file", "",
                                                            "Configuration ini file (*.ini *.INI)")
        if filename:
            print(filename)

    def export_config(self):
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Store configuration file", "",
                                                            "Configuration ini file (*.ini *.INI)")
        if filename:
            print(filename)

    def check_run_btn(self):
        self.__update_config()
        if self.config.check_sanity():
            self.Message.setText("")
            self.Run.setEnabled(True)
            self.Save.setEnabled(True)
            self.Export.setEnabled(True)
        else:
            self.Message.setText("Configuration is incomplete")
            self.Run.setEnabled(False)
            self.Save.setEnabled(False)
            self.Export.setEnabled(False)

    def __update_config(self):
        config: dict = self.config.get()
        config["P2P"]["host"] = self.host_field.text()
        config["P2P"]["password"] = self.password_field.text()
        config["P2P"]["peers"]: list = []
        for i in range(1, self.peer_fields+1):
            peer_i: QtWidgets.QLineEdit = self.__getattribute__("Peer%dInput" % i)
            if len(peer_i.text()):
                config["P2P"]["peers"].append(peer_i.text())
        self.config.set(config)

    def __disable_config(self):
        self.host_field.setEnabled(False)
        self.password_field.setEnabled(False)
        for i in range(1, self.peer_fields+1):
            peer_i: QtWidgets.QLineEdit = self.__getattribute__("Peer%dInput" % i)
            peer_i.setEnabled(False)
        self.covariant.setEnabled(False)

    def run_btn(self):
        self.__update_config()
        self.Message.setText("Waiting for all peers")
        self.__disable_config()

        self.Open.setEnabled(False)
        self.Save.setEnabled(False)
        self.Export.setEnabled(False)
        self.Run.setEnabled(False)
        self.Progress.show()
        self.Progress.setValue(0)

        self.thread = QtCore.QThread()
        self.worker = P2PWorker()

        self.worker.set_config(self.config.get()["P2P"])
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)

        self.worker.finished.connect(self.finishedWorker)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.progress.connect(self.reportProgress)
        self.worker.results.connect(self.gotResults)

        self.thread.start()

    def finishedWorker(self):
        self.Open.setEnabled(True)
        self.Run.setEnabled(True)
        self.Save.setEnabled(True)
        self.Export.setEnabled(True)

    def reportProgress(self, val: int):
        if val == 0:
            self.Progress.setValue(33)
            self.Message.setText("Broadcast strings")
        elif val == 1:
            self.Progress.setValue(66)
            self.Message.setText("Broadcast dictionaries")
        elif val == 2:
            self.Progress.setValue(100)
            self.Tabs.setTabVisible(1, True)
            self.Message.setText("Finished")

    def gotResults(self, result: object):
        self.Tabs.setTabVisible(1, True)
        self.Tabs.setCurrentIndex(1)
        self.ResultText.setText(str(result))


class P2PWorker(QtCore.QObject):

    finished = QtCore.pyqtSignal()
    progress = QtCore.pyqtSignal(int)
    results = QtCore.pyqtSignal(object)

    def set_config(self, config: dict):
        self.p2p_config = config

    def run(self):
        import random
        p2p = Runner(self.p2p_config)
        self.progress.emit(0)
        strings = p2p.broadcast_str("Test Message: %s" % random.randint(10, 99))
        print(strings)#
        self.progress.emit(1)
        my_msg = {"OK %d" % random.randint(0, 9): "V %d" % random.randint(0, 9)}
        dicts = p2p.broadcast_obj(my_msg)
        self.progress.emit(2)
        self.results.emit("own message: %s, received: %s" % (my_msg, dicts))

        self.finished.emit()


app = QtWidgets.QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()
