from dataclasses import dataclass
import logging
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))) # Add parent directory to path to load config class

from config import Config
from omegaconf import OmegaConf

@dataclass
class Debug():

    name: str
    config: Config
    level: logging.BASIC_FORMAT

    def __run__(self):
        #from config.config import Config 
        logging.basicConfig()
        logging.basicConfig(level=self.level)

        log = logging.getLogger(self.name)
        log.info("Start running")
        log.info("Configuration \n {}".format(OmegaConf.to_yaml(self.config)))

        return log