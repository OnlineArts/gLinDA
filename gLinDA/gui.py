from config import Config
from PyQt6 import QtWidgets, uic

import sys


class MainWindow(QtWidgets.QMainWindow):

    peer_fields: int = 4

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi("/home/roman/gui.ui", self)

        # gLinDA Configuration
        self.config: Config = Config(check_sanity=False)
        self._default_startup()

    def _default_startup(self):
        self.Tabs: QtWidgets.QTabWidget = self.TabWidget
        self.host_field: QtWidgets.QLineEdit = self.HostInput
        self.password_field: QtWidgets.QLineEdit = self.PasswordInput
        self.covariant: QtWidgets.QLineEdit = self.CovariantInput

        self.Message: QtWidgets.QLabel = self.MessageLabel
        self.Progress: QtWidgets.QProgressBar = self.ProgressBar
        self.Run: QtWidgets.QPushButton = self.RunButton
        self.Save: QtWidgets.QWidgetAction = self.actionSaveConfig
        self.Export: QtWidgets.QWidgetAction = self.actionExportConfig

        self.MessageLabel.setText("")
        self.Progress.hide()
        self.Run.setEnabled(False)
        self.Tabs.setTabVisible(1, False)
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
            self.MessageLabel.setText("")
            self.Run.setEnabled(True)
            self.Save.setEnabled(True)
            self.Export.setEnabled(True)
        else:
            self.MessageLabel.setText("Configuration is incomplete")
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

    def run_btn(self):
        import time
        self.MessageLabel.setText("Starting P2P network")
        self.Progress.show()

        self.__disable_config()
        print("RUN GLINDA!!")

        while self.Progress.value() < 100:
            self.Progress.setValue(self.Progress.value() + 25)
            time.sleep(1)

        self.Tabs.setTabVisible(1, True)
        self.Message.setText("Finished")

    def __disable_config(self):
        self.host_field.setEnabled(False)
        self.password_field.setEnabled(False)
        for i in range(1, self.peer_fields+1):
            peer_i: QtWidgets.QLineEdit = self.__getattribute__("Peer%dInput" % i)
            peer_i.setEnabled(False)
        self.covariant.setEnabled(False)

app = QtWidgets.QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()
