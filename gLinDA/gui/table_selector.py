from PyQt6 import QtWidgets


class TablePopUpDialog(QtWidgets.QDialog):

    filename = None
    cellname = None

    @staticmethod
    def write_df_to_qtable(df, table):
        headers = list(df)
        table.setRowCount(df.shape[0])
        table.setColumnCount(df.shape[1])
        table.setHorizontalHeaderLabels(headers)

        # getting data from df is computationally costly so convert it to array first
        df_array = df.values
        for row in range(df.shape[0]):
            for col in range(df.shape[1]):
                table.setItem(row, col, QtWidgets.QTableWidgetItem(str(df_array[row, col])))

    def setFilename(self, filename):
        self.filename = filename
        print(self.filename)

    def make(self):
        self.setWindowTitle("%s select an identifier" % self.filename)
        self.setMinimumSize(800, 590)
        layout = QtWidgets.QVBoxLayout()

        information_label = QtWidgets.QLabel(
            "To ensure gLinDA identifies the correct sample index, please verify that the meta table contains a column with all sample identifiers (IDs) and select the respective column. Apply the same procedure to the feature/OTU table. If necessary, you can transpose (flip) the table here.",
            self)
        information_label.setWordWrap(True)
        layout.addWidget(information_label)

        self.qttab = QtWidgets.QTableWidget()
        self.qttab.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)

        if self.filename is not None and len(self.filename):
            layout.addWidget(QtWidgets.QLabel("Currently selected identifier: %s" % self.cellname, self))
            self.tab = pd.read_csv(self.filename, nrows=100).T
            self.write_df_to_qtable(self.tab, self.qttab)

        layout.addWidget(self.qttab)
        horizontal_layout = QtWidgets.QHBoxLayout()

        confirm_btn = QtWidgets.QPushButton("Confirm")
        flip_btn = QtWidgets.QPushButton("Transpose")
        flip_btn.clicked.connect(self.flip_table)

        horizontal_layout.addWidget(flip_btn)
        horizontal_layout.addWidget(confirm_btn)
        layout.addLayout(horizontal_layout)

        self.setLayout(layout)