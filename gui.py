from sys import argv
from PyQt6 import QtWidgets

from gLinDA.gui.main import MainWindow

__version__ = "1.0.0"
__author__ = 'Roman Martin'
__credits__ = 'Heinrich Heine University Duesseldorf'


def main():
    app = QtWidgets.QApplication(argv)
    window = MainWindow()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
