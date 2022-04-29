###############################################################################
# BIDSme is a toolkit for bidsification of multy-modal neural imagery dataset
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
import sys
import logging
import time

from bidsme import exceptions
from bidsme.prepare import prepare
from bidsme.process import process
from bidsme.bidsify import bidsify
from bidsme.mapper import mapper

from bidsme.tools import config
from bidsme.tools import info
from bidsme.tools import paths


def init(level="INFO",
         formatter='%(name)s(%(lineno)d) - %(levelname)s %(message)s',
         quiet=False, log_dir=""):
    """
    Initialize logger and prints out bidsme header

    Parameters:
    -----------
    level: str
        Verbosity level of logger
    formatter: str
        Formatter string of logger
    quiet: bool
        If true, all terminal output are supressed,
        but log is still written to log file
    log_dir: str
        Directory where the log file is placed,
        if empty, no log file is written

    Returns:
    --------
    logger:
        the initialized logger object
    """

    logger = logging.getLogger()
    logger.name = os.path.splitext(os.path.basename(__file__))[0]
    info.setup_logging(logger,
                       level,
                       formatter,
                       quiet)
    if log_dir:
        info.addFileLogger(logger, log_dir)

    logger.info("")
    logger.info("-------------- START bidsme ----------------")
    logger.info("{}".format(time.asctime()))
    logger.info("programm version: {}".format(info.version()))
    logger.info("bids version: {}".format(info.bidsversion()))

    logger.debug("User: {}".format(paths.user))
    logger.debug("Application: {}".format(paths.app))
    logger.debug("Local dir: {}".format(paths.local))
    logger.debug("Instal dir: {}".format(paths.installation))
    logger.debug("Conf dir: {}".format(paths.config))

    return logger


def main(arguments: list):
    """
    Runs bidsme with command line arguments, stored in
    arguments list

    Parameters:
    -----------
    arguments: list
        list of command lines arguments, similar to
        sys.argv[1:]
    """

    prog, args = config.parseArgs(arguments)

    # checking paths
    if not os.path.isdir(args.source):
        raise NotADirectoryError("Source directory {} don't exists"
                                 .format(args.source))
    if not os.path.isdir(args.destination):
        raise NotADirectoryError("Destination directory {} don't exists"
                                 .format(args.destination))

    log_dir = os.path.join(args.destination, "code",
                           prog, args.cmd)
    logger = init(args.level, args.formatter, args.quiet, log_dir)

    code = 0

    try:
        if args.cmd == "prepare":
            prepare(source=args.source,
                    destination=args.destination,
                    plugin_file=args.plugin,
                    plugin_opt=args.plugin_opt,
                    sub_list=args.participants,
                    sub_skip_tsv=args.skip_in_tsv,
                    sub_skip_dir=args.skip_existing,
                    ses_skip_dir=args.skip_existing_sessions,
                    part_template=args.part_template,
                    sub_prefix=args.sub_prefix,
                    ses_prefix=args.ses_prefix,
                    sub_no_dir=args.no_subject,
                    ses_no_dir=args.no_session,
                    data_dirs=args.recfolder,
                    dry_run=args.dry_run
                    )
        elif args.cmd == "process":
            process(source=args.source,
                    destination=args.destination,
                    plugin_file=args.plugin,
                    plugin_opt=args.plugin_opt,
                    sub_list=args.participants,
                    sub_skip_tsv=args.skip_in_tsv,
                    sub_skip_dir=args.skip_existing,
                    ses_skip_dir=args.skip_existing_sessions,
                    part_template=args.part_template,
                    bidsmapfile=args.bidsmap,
                    dry_run=args.dry_run
                    )
        elif args.cmd == "bidsify":
            bidsify(source=args.source,
                    destination=args.destination,
                    plugin_file=args.plugin,
                    plugin_opt=args.plugin_opt,
                    sub_list=args.participants,
                    sub_skip_tsv=args.skip_in_tsv,
                    sub_skip_dir=args.skip_existing,
                    ses_skip_dir=args.skip_existing_sessions,
                    part_template=args.part_template,
                    bidsmapfile=args.bidsmap,
                    dry_run=args.dry_run
                    )
        elif args.cmd == "map":
            mapper(source=args.source,
                   destination=args.destination,
                   plugin_file=args.plugin,
                   plugin_opt=args.plugin_opt,
                   sub_list=args.participants,
                   sub_skip_tsv=args.skip_in_tsv,
                   sub_skip_dir=args.skip_existing,
                   ses_skip_dir=args.skip_existing_sessions,
                   process_all=args.process_all,
                   bidsmapfile=args.bidsmap,
                   map_template=args.template,
                   dry_run=args.dry_run
                   )
        else:
            raise ValueError("Invalid command")
    except Exception as err:
        code = exceptions.ReportError(err)
        logger.info("Command: {}".format(arguments))

    logger.info('-------------- FINISHED! -------------------')
    errors = info.reporterrors(logger)
    logger.info("Took {} seconds".format(time.process_time()))
    logger.info('--------------------------------------------')
    if code == 0 and errors > 0:
        logger.warning("Several errors detected but exit code is 0")
        code = 1
    return code


def cli_bidsme():
    """
    Funtion hook for setup-tools executable
    """
    res = main(sys.argv[1:])
    return(res)


def cli_bidsme_pdb():
    """
    Funtion hook for setup-tools executable with debugger
    """
    import pdb
    # pdb.set_trace()
    try:
        res = pdb.runcall(main, sys.argv[1:])
    except Exception:
        pdb.post_mortem()
        res = 1
    return 1
