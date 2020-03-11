import os
import sys
import logging

from tools import appdirs


logger = logging.getLogger(__name__)

user = os.getlogin()
app = os.path.splitext(os.path.basename(sys.argv[0]))[0]

local = os.getcwd()
installation = os.path.normpath(
        os.path.join(os.path.dirname(__file__), "../.."))

heuristics = os.path.join(installation, "heuristics")

config = appdirs.user_data_dir(app, user)


def findFile(fname, *kargs):
    path = ""
    found = False
    if os.path.isabs(fname):
        if os.path.isfile(fname):
            logger.debug("File {} found".format(fname))
            return fname
        else:
            logger.debug("File {} not found".format(fname))
            return ""
    for p in kargs:
        path = os.path.join(p, fname)
        if os.path.isfile(path):
            logger.debug("File {} found in {}".format(fname, p))
            found = True
            break
        logger.debug("File {} not found in {}".format(fname, p))
    if found:
        return path
    else:
        return ""
