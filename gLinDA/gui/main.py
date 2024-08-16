import pandas as pd
from os import path
from PyQt6 import QtWidgets, QtCore, uic, QtGui

from gLinDA.lib.config import Config
from gLinDA.gui.worker import gLinDALocalWorker, gLinDAP2PWorker
from gLinDA.lib.linda import LinDA
from gLinDA.gui.table_selector import TablePopUpDialog


class MainWindow(QtWidgets.QMainWindow):

    peer_fields: int = 5

    def __init__(self, config_args, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi("gLinDA/gui/gui.ui", self)

        # Icon
        self.setWindowIcon(QtGui.QIcon("gLinDA/gui/logo.png"))

        # P2P and threading
        self.thread = QtCore.QThread()
        self.worker = gLinDAP2PWorker()

        # gLinDA Configuration
        self._default_startup()
        self.config: Config = Config(config_args, check_sanity=False)
        self.__implement_config(self.config.get())
        self.__update_config()
        self.gLinDAResults = None

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
        self.ExportResult: QtWidgets.QWidgetAction = self.actionExportResults
        self.Tester: QtWidgets.QWidgetAction = self.actionNetworkTest

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
        self.featuretyp: QtWidgets.QComboBox = self.FeatureDataTypeCombo
        self.winsor: QtWidgets.QComboBox = self.WinsorCombo
        self.outlier: QtWidgets.QLineEdit = self.OutlierPctInput
        self.zero_handling: QtWidgets.QComboBox = self.ZeroHandlingInput
        self.correction: QtWidgets.QLineEdit = self.CorrectionInput
        self.meanabund: QtWidgets.QLineEdit = self.MeanAbundanceInput
        self.maxabund: QtWidgets.QLineEdit = self.MaxAbundanceInput
        self.prev: QtWidgets.QLineEdit = self.PrevalenceInput

        # Results tab
        self.ResultText: QtWidgets.QTextBrowser = self.ResultBrowser

        # Footer
        self.Message: QtWidgets.QLabel = self.MessageLabel
        self.Progress: QtWidgets.QProgressBar = self.ProgressBar
        self.Run: QtWidgets.QPushButton = self.RunButton

        # Popup
        self.FeaturePopupButton: QtWidgets.QToolButton = self.FeatureIndex
        self.MetaPopupButton: QtWidgets.QToolButton = self.MetaIndex
        # self.FeaturePopupButton.clicked.connect(self.show_table_selector)
        # self.MetaPopupButton.clicked.connect(self.show_table_selector)

        # Default values
        self.Message.setText("")
        self.Progress.hide()
        self.Run.setEnabled(False)
        self.Tabs.setTabVisible(1, False)  # Index 1: Results
        self.Save.setEnabled(False)
        self.Export.setEnabled(False)
        self.ExportResult.setEnabled(False)
        self.FeaturePopupButton.setEnabled(False)
        self.MetaPopupButton.setEnabled(False)
        self.Tester.setEnabled(False)
        # TODO: Debug
        self.rsa.setChecked(False)
        self.rsa.setEnabled(False)
        self.aes.setChecked(True)

    def show_table_selector(self):
        tbl_sel = TablePopUpDialog()
        tbl_sel.setFilename(self.config.get()["LINDA"]["feature_table"])
        tbl_sel.make()
        tbl_sel.exec()

    def open_network_tester(self):
        pass

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
            self.featuredata.setText("Feature Table: %s" % path.basename(filename))
            cfg: dict = self.config.get()
            cfg["LINDA"]["feature_table"] = filename
            self.config.set(cfg)
            self.check_run_btn()

    def select_metadata(self):
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Open a metadata table file",
            "", "Table file (*.csv *.CSV *.xls *.XLS)")
        if filename:
            self.metadata.setText("Meta Data: %s" % path.basename(filename))
            cfg: dict = self.config.get()
            cfg["LINDA"]["meta_table"] = filename
            self.config.set(cfg)
            self.check_run_btn()

    def __implement_config(self, config: dict):
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

        # LINDA
        if (config["LINDA"]["formula"] is not None and type(config["LINDA"]["formula"]) is str
                and len(config["LINDA"]["formula"])):
            self.covariates.setText(config["LINDA"]["formula"])

        if config["LINDA"]["feature_table"] is not None and type(config["LINDA"]["feature_table"]) is str and \
            path.exists(config["LINDA"]["feature_table"]):
            self.featuredata.setText("Feature Table: %s" % path.basename(config["LINDA"]["feature_table"]))
            #self.FeaturePopupButton.setEnabled(True)

        if config["LINDA"]["meta_table"] is not None and type(config["LINDA"]["meta_table"]) is str and \
            path.exists(config["LINDA"]["meta_table"]):
            self.metadata.setText("Meta Data: %s" % path.basename(config["LINDA"]["meta_table"]))
            #self.MetaPopupButton.setEnabled(True)

        if config["LINDA"]["prevalence"] is not None:
            self.prev.setText(str(config["LINDA"]["prevalence"]))

        if config["LINDA"]["mean_abundance"] is not None and len(str(config["LINDA"]["mean_abundance"])):
            self.meanabund.setText(str(config["LINDA"]["mean_abundance"]))

        if config["LINDA"]["max_abundance"] is not None and len(str(config["LINDA"]["max_abundance"])):
            self.maxabund.setText(str(config["LINDA"]["max_abundance"]))

        if config["LINDA"]["outlier_percentage"] is not None and len(str(config["LINDA"]["outlier_percentage"])):
            self.outlier.setText(str(config["LINDA"]["outlier_percentage"]))

        if config["LINDA"]["correction_cutoff"] is not None and len(str(config["LINDA"]["correction_cutoff"])):
            self.correction.setText(str(config["LINDA"]["correction_cutoff"]))

        # Have to be the last otherwise artefacts will occur
        if config["P2P"]["solo_mode"] is not None and type(config["P2P"]["solo_mode"]) is bool:
            self.solo.setChecked(config["P2P"]["solo_mode"])
            self.solo_mode()


    def __import_config_file(self, config_path: str):
        """
        Import a configuration file and update the configuration fields.
        :param config_path: path to the INI configuration file.
        """
        # P2P
        self.config: Config = Config(ini_path=config_path, check_sanity=False)
        config = self.config.get()
        self.__implement_config(config)

    def save_config(self):
        """
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

    def export_results(self):
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Store results", "",
                                                            "Text file (*.txt *.TXT)")
        results, formatted_result = self.gLinDAResults

        if filename and results is not None:
            with open(filename, "w") as file_result_txt:
                file_result_txt.write(formatted_result)
                file_result_txt.close()

            if len(results):
                for key, value in results.items():
                    new_file_name = "%s_%s.csv" % (filename[:filename.rfind("."):], key)
                    res: pd.DataFrame = value
                    res.to_csv(new_file_name)

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
        if len(self.covariates.text()):
            config["LINDA"]["formula"] = self.covariates.text()
        config["LINDA"]["prevalence"] = self.prev.text()

        config["LINDA"]["mean_abundance"] = self.meanabund.text()
        config["LINDA"]["max_abundance"] = self.maxabund.text()
        config["LINDA"]["outlier_percentage"] = self.outlier.text()
        config["LINDA"]["correction_cutoff"] = self.correction.text()

        self.config.set(config)
        # TODO: Debug, remove later
        self.rsa.setChecked(False)
        self.rsa.setEnabled(False)
        self.aes.setChecked(True)

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
        self.featuredata.setEnabled(status)
        self.metadata.setEnabled(status)

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
        self.__update_config()
        self.config.cast_parameters()

        if self.solo.isChecked():
            # Solo mode
            self._run_solo_gLinDA()  # placeholder currently
        else:
            self._run_p2p_gLinDA()

    def _run_p2p_gLinDA(self):
        """
        Triggers the gLinDA execution in a separated thread
        """
        self.Message.setText("Waiting for all peers")
        self.__config_p2p_fields_status(False)
        self.__config_linda_fields_status(False)
        self.__menu_bar_status(False)

        # Show up progress bar
        self.Progress.show()
        self.Progress.setValue(0)

        # Preparing Threading an P2P network
        self.thread = QtCore.QThread()  # refresh the threads (they got deleted after each round)
        self.worker = gLinDAP2PWorker()  # same here

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
        """
        Triggers the gLinDA execution in a separated thread
        """
        self.Message.setText("Run local LinDA")
        self.__config_p2p_fields_status(False)
        self.__config_linda_fields_status(False)
        self.__menu_bar_status(False)

        # Show up progress bar
        self.Progress.show()
        self.Progress.setValue(0)

        # Preparing Threading for LinDA
        self.thread = QtCore.QThread()  # refresh the threads (they got deleted after each round)
        self.worker = gLinDALocalWorker()  # same here

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

    def worker_finished(self):
        """
        Resets all configuration menus
        """
        self.__menu_bar_status(True)
        self.__config_p2p_fields_status(True)
        self.__config_linda_fields_status(True)
        self.solo_mode()
        self.Progress.hide()

    def worker_progress_update(self, val: int):
        """
        Updates the current progress state
        :param val: integer indicate the current state
        """
        if self.config.get()["P2P"]["solo_mode"]:
            if val == 0:
                self.Progress.setValue(33)
                self.Message.setText("Building models")
            elif val == 1:
                self.Progress.setValue(66)
                self.Message.setText("Finished models")
            elif val == 2:
                self.Progress.setValue(100)
                self.Message.setText("Finished")

        else:
            if val == 0:
                self.Progress.setValue(25)
                self.Message.setText("Building models")
            elif val == 1:
                self.Progress.setValue(50)
                self.Message.setText("Initialize P2P network")
            elif val == 2:
                self.Progress.setValue(75)
                self.Message.setText("Sharing parameters")
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
        self.ResultText.setEnabled(True)
        formatted_results = LinDA.display_results(result)
        self.ResultText.setText(formatted_results)
        self.ExportResult.setEnabled(True)
        self.gLinDAResults = [result, formatted_results]

    def solo_mode(self):
        """
        Disable or enable the P2P configuration fields
        """
        if self.solo.isChecked():
            self.__config_p2p_fields_status(False)
        else:
            self.__config_p2p_fields_status(True)
        self.check_run_btn()