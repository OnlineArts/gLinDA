from linda import LinDa
from glinda import gLinDAWrapper
from lib.p2p import gLinDAP2P, gLinDAKeyring, gLinDAP2Prunner
from lib.config import gLinDAConfig
from lib.p2p_client import gLinDAclient
from lib.p2p_server import gLinDAserver

from .core import *

"""
gLinDA

gLinDA is a gossip learning implementation of LinDA. In contrast to LinDA, it is entirely written in Python and 
royalty-free licensed.
"""

__version__ = "0.5.0"
__author__ = 'Leon Fehse, Mohammad Tajabadi, Roman Martin, Dominik Heider'
__credits__ = 'Heinrich Heine University Duesseldorf'
