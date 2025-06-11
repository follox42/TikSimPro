# To implement eventually


import os
import time
import pickle
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
import random
from pathlib import Path

from src.publishers.base_publisher import IPublisher
#from connectors.instagram_connector import InstagramConnector

logger = logging.getLogger("TikSimPro")

class InstagramPublisher(IPublisher):
    """
    Publisher for instagram
    """
    def __init__(self, 
                credentials_file: Optional[str] = None, 
                auto_close: bool = True,
                headless: bool = False):
        pass

    