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

import exceptions
from prepare import prepare
from process import process
from bidsify import bidsify
from mapper import mapper

from tools import config
from tools import info
from tools import paths


if __name__ == "__main__":

    prog, args = config.parseArgs(sys.argv[1:])

    # checking paths
    if not os.path.isdir(args.source):
        raise NotADirectoryError("Source directory {} don't exists"
                                 .format(args.source))
    if not os.path.isdir(args.destination):
        raise NotADirectoryError("Destination directory {} don't exists"
                                 .format(args.destination))

    code = 0

    logger = logging.getLogger()
    logger.name = os.path.splitext(os.path.basename(__file__))[0]
    info.setup_logging(logger,
                       args.level,
                       args.formatter,
                       args.quiet)
    log_dir = os.path.join(args.destination, "code",
                           prog, args.cmd)
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
                   bidsmapfile=args.bidsmap,
                   map_template=args.template,
                   dry_run=args.dry_run
                   )
        else:
            raise ValueError("Invalid command")
    except Exception as err:
        code = exceptions.ReportError(err)
        logger.info("Command: {}".format(os.sys.argv))

    logger.info('-------------- FINISHED! -------------------')
    errors = info.reporterrors(logger)
    logger.info("Took {} seconds".format(time.process_time()))
    logger.info('--------------------------------------------')
    if code == 0 and errors > 0:
        logger.warning("Several errors detected but exit code is 0")
        code = 1
    os.sys.exit(code)
