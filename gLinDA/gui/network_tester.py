import matplotlib
import networkx as nx
import matplotlib.pyplot as plt

from PyQt6 import QtWidgets
matplotlib.use('QtAgg')

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure


class NetworkTester(QtWidgets.QDialog):

    host: str = ""
    peers: list = []
    textbox: QtWidgets.QTextBrowser = None

    figure = plt.figure()

    def setPeers(self, host: host, peers: list):
        self.host = host
        self.peers = peers

    def draw_network(self):
        self.figure.clf()

        g = nx.Graph()
        g.add_edge(1, 2)
        g.add_edge(2, 3)
        g.add_edge(3, 4)
        g.add_edge(1, 4)
        g.add_edge(1, 5)

        random_pos = nx.random_layout(g, seed=42)
        pos = nx.spring_layout(g, pos=random_pos)
        nx.draw(g, pos)
        self.canvas.draw_idle()

    def __init__(self):
        super(NetworkTester, self).__init__()
        self.init_ui()

    def init_ui(self):
        self.figure = plt.figure()
        self.canvas = FigureCanvasQTAgg(self.figure)

        self.setWindowTitle("Network Tester")
        self.setMinimumSize(800, 590)

        # Basic layout
        layout = QtWidgets.QVBoxLayout()
        confirm_btn = QtWidgets.QPushButton("Confirm")

        # Textbox
        self.textbox = QtWidgets.QTextBrowser()

        # graph + text
        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(self.canvas)
        hlayout.addWidget(self.textbox)

        layout.addLayout(hlayout)
        layout.addWidget(confirm_btn)

        self.setLayout(layout)
        self.draw_network()
        self.show()

    def make(self):
        self.draw_network()
