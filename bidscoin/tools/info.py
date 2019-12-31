import os
import logging
import coloredlogs

class CallCounted:
    """Decorator to determine number of calls for a method"""

    def __init__(self,method):
        self.method=method
        self.counter=0

    def __call__(self,*args,**kwargs):
        self.counter+=1
        return self.method(*args,**kwargs)

class MsgCounterHandler(logging.Handler):
    level2count = None

    def __init__(self, *args, **kwargs):
        super(MsgCounterHandler, self).__init__(*args, **kwargs)
        self.level2count = {}

    def emit(self, record):
        l = record.levelname
        if (l not in self.level2count):
            self.level2count[l] = 0
        self.level2count[l] += 1


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
                  log_dir: str = "",  
                  level: str = 'INFO') -> None:
    """
    Setup the logging

    :param logger:      Logger to setup
    :param log_dir:     Name of the logdir, will be created if not existing
    :param level:       Logger level
     """

    # Set the format and logging level
    fmt = '%(asctime)s - %(name)s(%(lineno)d) - %(levelname)s %(message)s'
    datefmt = '%Y-%m-%d %H:%M:%S'
    formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)
    logger.setLevel(level)

    counthandler = MsgCounterHandler()
    counthandler.setLevel(logging.WARNING)
    counthandler.set_name('counthangler')

    logger.addHandler(counthandler)

    # Create the log dir if it does not exist
    if log_dir != "":
        os.makedirs(log_dir, exist_ok=True)

        log_file = os.path.join(log_dir, logger.name + '.log')
        error_file = os.path.join(log_dir, logger.name + '.err')

        # Set & add the log filehandler
        loghandler = logging.FileHandler(log_file, mode="w")
        loghandler.setLevel(level)
        loghandler.setFormatter(formatter)
        loghandler.set_name('loghandler')
        logger.addHandler(loghandler)

        # Set & add the error / warnings handler
        errorhandler = logging.FileHandler(error_file, mode='w')
        errorhandler.setLevel(logging.WARNING)
        errorhandler.setFormatter(formatter)
        errorhandler.set_name('errorhandler')
        logger.addHandler(errorhandler)

    # Set & add the streamhandler and 
    # add some color to those boring terminal logs! :-)
    coloredlogs.install(level=level, fmt=fmt, datefmt=datefmt)


def reporterrors(logger):
    for handler in logger.handlers:
        if isinstance(handler,MsgCounterHandler):
            logger.info("{}:{}"
                        .format(handler.name, handler.level2count))
        if isinstance(handler, logging.FileHandler):
            logger.info("{}:{}".format(handler.name, handler.baseFilename))
