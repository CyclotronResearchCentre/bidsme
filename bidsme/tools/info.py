###############################################################################
# info.py contains set of classes and functions to manage logging
###############################################################################
# Copyright (c) 2019-2020, University of Liège
# Author: Nikita Beliy
# Owner: Liege University https://www.uliege.be
# Credits: [Marcel Zwiers]
# Maintainer: Nikita Beliy
# Email: Nikita.Beliy@uliege.be
# Status: developpement
###############################################################################
# This file is part of BIDSme
# BIDSme is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
# eegBidsCreator is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with BIDSme.  If not, see <https://www.gnu.org/licenses/>.
##############################################################################


import os
import logging
import coloredlogs

fmt = '%(asctime)s - %(name)s(%(lineno)d) - %(levelname)s %(message)s'
datefmt = '%Y-%m-%d %H:%M:%S'
formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)


class CallCounted:
    """Decorator to determine number of calls for a method"""

    def __init__(self, method):
        self.method = method
        self.counter = 0

    def __call__(self, *args, **kwargs):
        self.counter += 1
        return self.method(*args, **kwargs)


class MsgCounterHandler(logging.Handler):
    level2count = None

    def __init__(self, *args, **kwargs):
        super(MsgCounterHandler, self).__init__(*args, **kwargs)
        self.level2count = {}

    def emit(self, record):
        lvl = record.levelname
        if (lvl not in self.level2count):
            self.level2count[lvl] = 0
        self.level2count[lvl] += 1


def bidsversion() -> str:
    """
    Reads the BIDS version from the BIDSVERSION.TXT file

    :return:    The BIDS version number
    """

    with open(os.path.join(os.path.dirname(__file__),
                           "../..",
                           'bidsversion.txt')) as fid:
        version = fid.read().strip()

    return str(version)


def version() -> str:
    """
    Reads the BIDSCOIN version from the VERSION.TXT file

    :return:    The BIDSCOIN version number
    """

    with open(os.path.join(os.path.dirname(__file__),
                           "../..",
                           'version.txt')) as fid:
        version = fid.read().strip()

    return str(version)


def setup_logging(logger: logging.Logger,
                  level: str = 'INFO',
                  fmt: str = fmt,
                  quiet: bool = False) -> None:
    """
    Setup the logging

    :param logger:      Logger to setup
    :param level:       Logger level
     """

    # Set the format and logging level
    logger.setLevel(level)

    counthandler = MsgCounterHandler()
    counthandler.setLevel(logging.WARNING)
    counthandler.set_name('counthangler')

    logger.addHandler(counthandler)

    global formatter
    formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)

    # Set & add the streamhandler and
    # add some color to those boring terminal logs! :-)
    if not quiet:
        coloredlogs.install(level=level, fmt=fmt, datefmt=datefmt)


def addFileLogger(logger, log_dir):
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, logger.name + '.log')
    error_file = os.path.join(log_dir, logger.name + '.err')

    # Set & add the log filehandler
    loghandler = logging.FileHandler(log_file, mode="w")
    loghandler.setLevel(logger.level)
    loghandler.setFormatter(formatter)
    loghandler.set_name('loghandler')
    logger.addHandler(loghandler)

    # Set & add the error / warnings handler
    errorhandler = logging.FileHandler(error_file, mode='w')
    errorhandler.setLevel(logging.WARNING)
    errorhandler.setFormatter(formatter)
    errorhandler.set_name('errorhandler')
    logger.addHandler(errorhandler)


def reporterrors(logger):
    errors = 0
    for handler in logger.handlers:
        if isinstance(handler, MsgCounterHandler):
            logger.info("{}:{}"
                        .format(handler.name, handler.level2count))
            errors = handler.level2count.get('ERROR', 0)
        if isinstance(handler, logging.FileHandler):
            logger.info("{}:{}".format(handler.name, handler.baseFilename))
    return errors
