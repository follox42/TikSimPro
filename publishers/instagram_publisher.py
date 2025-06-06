# To implement eventually


import os
import time
import pickle
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
import random
from pathlib import Path

from core.interfaces import IContentPublisher
#from connectors.instagram_connector import InstagramConnector

logger = logging.getLogger("TikSimPro")

class InstagramPublisher(IContentPublisher):
    """
    Publisher for instagram
    """
    def __init__(self, 
                credentials_file: Optional[str] = None, 
                auto_close: bool = True,
                headless: bool = False):
        pass

    