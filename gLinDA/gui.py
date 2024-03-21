from config import Config
from p2p import Runner
from PyQt6 import QtWidgets, QtCore, uic, QtGui
from os import path
import sys

class MainWindow(QtWidgets.QMainWindow):

    peer_fields: int = 5

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi("gui.ui", self)

        # Icon
        self.setWindowIcon(QtGui.QIcon("logo.png"))

        # P2P and threading
        self.thread = QtCore.QThread()
        self.worker = gLinDAWorker()

        # gLinDA Configuration
        self.config: Config = Config(check_sanity=False)
        self._default_startup()

    def _default_startup(self):
        """
        Defines default GUI elements
        """

        # Basic layout
        self.Tabs: QtWidgets.QTabWidget = self.TabWidget

        # Menu bar
        self.Open: QtWidgets.QWidgetAction = self.actionOpenConfig
        self.Save: QtWidgets.QWidgetAction = self.actionSaveConfig
        self.Export: QtWidgets.QWidgetAction = self.actionExportConfig

        # Configuration tab
        ## P2P
        self.host_field: QtWidgets.QLineEdit = self.HostInput
        self.password_field: QtWidgets.QLineEdit = self.PasswordInput
        self.aes: QtWidgets.QRadioButton = self.AESEncryption
        self.rsa: QtWidgets.QRadioButton = self.RSAEncryption
        self.solo: QtWidgets.QCheckBox = self.SoloMode

        # LinDA
        self.covariates: QtWidgets.QLineEdit = self.CovariatesInput
        self.featuredata: QtWidgets.QLineEdit = self.FeatureDataTableButton
        self.metadata: QtWidgets.QLineEdit = self.MetaDataTableButton

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
        self.rsa.setChecked(True)

    def load_configuration_file(self):
        """
        This function will be triggered by the "Open" dialog.
        """
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Open a gLinDA configuration file",
            "", "Configuration ini file (*.ini *.INI)")
        if filename:
            self.__import_config_file(filename)

    def select_feature_data(self):
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Open a feature data table file",
            "", "Table file (*.csv *.CSV *.xls *.XLS)")
        if filename:
            self.featuredata.setText(path.basename(filename))
            cfg: dict = self.config.get()
            cfg["LINDA"]["feature_table"] = filename
            self.config.set(cfg)
            self.check_run_btn()

    def select_metadata(self):
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Open a metadata table file",
            "", "Table file (*.csv *.CSV *.xls *.XLS)")
        if filename:
            self.metadata.setText(path.basename(filename))
            cfg: dict = self.config.get()
            cfg["LINDA"]["metadata_table"] = filename
            self.config.set(cfg)
            self.check_run_btn()

    def hover_run_button(self):
        print("here!")

    def __import_config_file(self, config_path: str):
        """
        Import a configuration file and update the configuration fields.
        :param config_path: path to the INI configuration file.
        """

        ## P2P
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

        if config["P2P"]["asymmetric"] is not None and type(config["P2P"]["asymmetric"]) is bool:
            if config["P2P"]["asymmetric"]:
                self.rsa.setChecked(True)
                self.aes.setChecked(False)
            else:
                self.aes.setChecked(True)
                self.rsa.setChecked(False)

        if config["P2P"]["solo_mode"] is not None and type(config["P2P"]["solo_mode"]) is bool:
            self.solo.setChecked(config["P2P"]["solo_mode"])
            self.solo_mode()

        ## LINDA
        if config["LINDA"]["formula"] is not None and type(config["LINDA"]["formula"]) is str and len(config["LINDA"]["formula"]):
            self.covariates.setText(config["LINDA"]["formula"])

        if config["LINDA"]["feature_table"] is not None and type(config["LINDA"]["feature_table"]) is str and \
            path.exists(config["LINDA"]["feature_table"]):
            self.featuredata.setText(path.basename(config["LINDA"]["feature_table"]))

        if config["LINDA"]["metadata_table"] is not None and type(config["LINDA"]["metadata_table"]) is str and \
            path.exists(config["LINDA"]["metadata_table"]):
            self.metadata.setText(path.basename(config["LINDA"]["metadata_table"]))

        self.check_run_btn()

    def save_config(self):
        """
        TODO: stores the configuration as shown in the GUI.
        :return:
        """
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Store configuration file", "",
                                                            "Configuration ini file (*.ini *.INI)")
        if filename:
            self.config.save_config_to_file(filename)

    def export_config(self):
        """
        This is required for auto-detection for the own host address, by that one configuration can be shared through
        all peers.
        """
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Store configuration file", "",
                                                            "Configuration ini file (*.ini *.INI)")
        if filename:
            cfg: dict = self.config.get()
            host = cfg["P2P"].pop("host")
            cfg["P2P"]["peers"].append(host)
            cfg["P2P"]["solo_mode"] = False
            new_cfg: Config = Config(check_sanity=False)
            new_cfg.set(cfg)
            new_cfg.save_config_to_file(filename)

    def check_run_btn(self):
        """
        Check whether the run button should be clickable (enabled).
        """
        self.__update_config()

        # Check if the configuration seems to be valid and complete
        if self.config.check_sanity():
            self.Message.setText("")
            self.Run.setEnabled(True)
            self.Save.setEnabled(True)
            self.Export.setEnabled(True)
        else:
            if len(self.config.msg):
                self.Run.setToolTip(self.config.msg)
            self.Run.setEnabled(False)
            self.Save.setEnabled(False)
            self.Export.setEnabled(False)

    def __update_config(self):
        """
        Overwrite the config object with GUI config fields
        """
        config: dict = self.config.get()

        # P2P
        config["P2P"]["host"] = self.host_field.text()
        config["P2P"]["password"] = self.password_field.text()
        config["P2P"]["peers"]: list = []
        for i in range(1, self.peer_fields+1):
            peer_i: QtWidgets.QLineEdit = self.__getattribute__("Peer%dInput" % i)
            if len(peer_i.text()):
                config["P2P"]["peers"].append(peer_i.text())
        config["P2P"]["solo_mode"] = self.solo.isChecked()

        # LINDA
        config["LINDA"]["alpha"] = self.AlphaInput.text()

        self.config.set(config)

    def __config_p2p_fields_status(self, status: bool = False):
        """
        Disables or enables all configuration fields.
        :param status: True to enable
        """
        self.host_field.setEnabled(status)
        self.password_field.setEnabled(status)
        for i in range(1, self.peer_fields+1):
            peer_i: QtWidgets.QLineEdit = self.__getattribute__("Peer%dInput" % i)
            peer_i.setEnabled(status)
        self.aes.setEnabled(status)
        self.rsa.setEnabled(status)

    def __config_linda_fields_status(self, status: bool = False):
        self.covariates.setEnabled(status)

    def __menu_bar_status(self, status: bool = False):
        """
        Disables or enables all menu bar actions.
        :param status: True to enable
        """
        self.Open.setEnabled(status)
        self.Run.setEnabled(status)
        self.Save.setEnabled(status)
        self.Export.setEnabled(status)

    def run_btn(self):
        """
        Triggers the gLinDA P2P or Solo Mode execution
        """
        if self.solo.isChecked():
            # Solo mode
            self._run_solo_gLinDA()  # placeholder currently
        else:
            self._run_p2p_gLinDA()

    def _run_p2p_gLinDA(self):
        """
        Triggers the gLinDA execution in a separated thread
        """
        self.__update_config()
        self.Message.setText("Waiting for all peers")
        self.__config_p2p_fields_status(False)
        self.__config_linda_fields_status(False)
        self.__menu_bar_status(False)

        # Show up progress bar
        self.Progress.show()
        self.Progress.setValue(0)

        # Preparing Threading an P2P network
        self.thread = QtCore.QThread()  # refresh the threads (they got deleted after each round)
        self.worker = gLinDAWorker()  # same here

        self.worker.set_config(self.config.get())  # Sets the configuration
        self.worker.moveToThread(self.thread)

        # Defines the callback functions for the threads and workers
        self.thread.started.connect(self.worker.run)
        self.thread.finished.connect(self.thread.deleteLater)

        self.worker.finished.connect(self.worker_finished)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.progress.connect(self.worker_progress_update)
        self.worker.results.connect(self.worker_results_presentation)

        # Starts all threads
        self.thread.start()

    def _run_solo_gLinDA(self):
        """
        Triggers the gLinDA solo mode execution in a separated thread
        """
        # placeholder #
        pass

    def worker_finished(self):
        """
        Resets all configuration menus
        """
        self.__menu_bar_status(True)
        self.__config_p2p_fields_status(True)
        self.__config_linda_fields_status(True)
        self.Progress.hide()

    def worker_progress_update(self, val: int):
        """
        Updates the current progress state
        :param val: integer indicate the current state
        """
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

    def worker_results_presentation(self, result: object):
        """
        Shows the results from the gLinDAWorker computations.
        :param result:
        """
        self.Tabs.setTabVisible(1, True)
        self.Tabs.setCurrentIndex(1)
        self.ResultText.setText(str(result))

    def solo_mode(self):
        """
        Disable or enable the P2P configuration fields
        """
        if self.solo.isChecked():
            self.__config_p2p_fields_status(False)
        else:
            self.__config_p2p_fields_status(True)
        self.check_run_btn()


class gLinDAWorker(QtCore.QObject):
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
        my_msg = {"OK %d" % random.randint(0, 9): "V %d" % random.randint(0, 9)}
        dicts = p2p.broadcast_obj(my_msg)
        self.progress.emit(2)
        self.results.emit("own message: %s, received: %s" % (my_msg, dicts))

        self.finished.emit()


def main():
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()