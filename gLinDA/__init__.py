from .linda import LinDA
from .glinda import gLinDAWrapper
from .config import gLinDAConfig
from .p2p import gLinDAP2P, gLinDAKeyring, gLinDAP2Prunner
from .p2p_client import gLinDAclient
from .p2p_server import gLinDAserver

"""
gLinDA

gLinDA is a gossip learning implementation of LinDA. In contrast to LinDA, it is entirely written in Python and 
royalty-free licensed.
"""

__version__ = "0.5.0"
__author__ = 'Leon Fehse, Mohammad Tajabadi, Roman Martin, Dominik Heider'
__credits__ = 'Heinrich Heine University Duesseldorf'
