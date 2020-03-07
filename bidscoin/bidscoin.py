#!/usr/bin/env python
import os
import sys
import logging
import time
import traceback

import exceptions
from tools import config
from tools import info 



if __name__ == "__main__":


    args = config.parseArgs(sys.argv[1:])
    print(args)

    logger = logging.getLogger()
    logger.name = os.path.splitext(os.path.basename(__file__))[0]
    info.setup_logging(logger, 'INFO')
    info.addFileLogger(logger, 
                       os.path.join(args.destination,
                                    "code", 
                                    sys.argv[0],
                                    args.cmd))

    # checking paths
    if not os.path.isdir(args.source):
        logger.critical("Source directory {} don't exists"
                        .format(args.source))
        raise NotADirectoryError(args.source)
    if not os.path.isdir(args.destination):
        logger.critical("Destination directory {} don't exists"
                        .format(args.destination))
        raise NotADirectoryError(args.destination)

    code = 0
    logger.info("")
    logger.info("-------------- START bidscoin --------------")
    logger.info("{}".format(time.asctime()))
    logger.info("programm version: ".format(info.version()))
    logger.info("bids version: ".format(info.bidsversion()))

    try:
        if args.cmd == "prepare":
            pass
        elif args.cmd == "bidsify":
            pass
        elif args.cmd == "map":
            pass
        else:
            raise ValueError("Invalid command")
    except Exception as err:
        if isinstance(err, exceptions.CoinException):
            code = err.base + err.code
        else:
            code = 1
        exc_type, exc_value, exc_traceback = os.sys.exc_info()
        tr = traceback.extract_tb(exc_traceback)
        for l in tr:
            logger.error("{}({}) in {}: "
                         .format(l[0], l[1], l[2]))
        logger.error("{}:{}: {}".format(code, exc_type.__name__, exc_value))
        logger.info("Command: {}".format(os.sys.argv))

    logger.info('-------------- FINISHED! -------------------')
    errors = info.reporterrors(logger)
    logger.info("Took {} seconds".format(time.process_time()))
    logger.info('--------------------------------------------')
    if code == 0 and errors > 0:
        logger.warning("Several errors detected but exit code is 0")
        code = 1
    os.sys.exit(code)
