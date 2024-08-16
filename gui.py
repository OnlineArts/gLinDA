#!/bin/env python3

from sys import argv
from PyQt6 import QtWidgets

from gLinDA.gui.main import MainWindow
from gLinDA.lib.argument import Arguments

__version__ = "1.0.0"
__author__ = 'Roman Martin'
__credits__ = 'Heinrich Heine University Duesseldorf'


def main():
    parser = Arguments()
    app = QtWidgets.QApplication(argv)
    window = MainWindow(parser.get_args())
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
