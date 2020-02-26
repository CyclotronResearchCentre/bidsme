import os
import logging

from tools.yaml import yaml
from tools.config_default import config

logger = logging.getLogger(__name__)

def exportConfig(filename: str) -> None:
    with open(filename, "w") as f:
        yaml.dump(config, f)

def loadConfig(filename: str) -> None:
    with open(filename, "r") as f:
        try:
            yaml_map = yaml.load(f)
        except Exception as e:
            err = sys.exc_info()
            logger.error("Failed to load configuration from {}"
                         .format(filename))
            logger.error("{}: {}".format(err[0], err[1]))
            raise


