###############################################################################
# dcm2niix.py contains tools, that can be used in user plugins,
# that can be used to convert DICOM to NIFTY formats on fly
# these tools do require dcm2niix module installed
###############################################################################
# Copyright (c) 2019-2023, University of Liège
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
import shutil
import json
import re
import dcm2niix

from subprocess import run
from bidsme.tools import tools
from bidsme.Modules import baseModule

logger = logging.getLogger(__name__)


def convert(outfolder: str, binary=None, echo=False, remove=True,
            **kwargs):
    """
    Use dcm2niix (https://github.com/rordenlab/dcm2niix)
    to convert DICOM files to NIFTY.

    If use_dump is True, the header dump will be complemented
    by metadata extracted by dcm2niix in the custom section
    of the header, and output files will be identified by
    bidsme as bidsmeNIFTY files. Due to technical limitations,
    the files will be renamed into <SequenceId>.IMA files.

    If use_dump is False, the default json files from conversion
    will be preserved and output files will be identified as
    jsonNIFTY.

    This tool is intended to be used in preparation step
    in SequenceEndEP.

    Parameters:
    -----------
    outfolder: str
        path to output folder where data files has been copied
    recording: baseModule
        recording object to convert
    use_dump: bool
        To conserve header dump json file (True) or
        to ignore it (False). Conserving header dump file
        will also rename dicom files to convert.
        Default: True

    Returns:
    --------
    None

    Example:
    --------
    # In SequenceEndEP, given
    #   recording is BaseModule object
    #   outfolder is the path where files are copied
    from bidsme.plugins.tools import dcm2niix
    if not dry_run:
        dcm2niix.convert(outfolder, recording)
    """
    # Testing dcm2niix executable
    if not binary:
        binary = dcm2niix.bin
    try: 
        p = run([binary] + ["--version"], capture_output=True, text=True)
    except FileNotFoundError as err:
        logger.error("Can't find dcm2niix executable at {}".format(binary))
        raise
    logger.info(p.stdout.split("\n")[0])

    # Building up dcm2niix parameters
    kwargs.update(v=1)
    dcm2niix_options = [binary]
    for arg, val in kwargs.items():
        if len(arg) > 1:
            arg = "--" + arg
        else:
            arg = "-" + arg
        dcm2niix_options.append(arg)
        if val is not None:
            dcm2niix_options.append(str(val))
    dcm2niix_options.append(outfolder)
    print(dcm2niix_options)
    p = run(dcm2niix_options, capture_output=True, text=True)
    if p.returncode != 0:
        logger.error("dcm2niix failed with error code {}".format(p.returncode))
        logger.error("stderr:\n{}".format(p.stderr))
        logger.info("stdout:\n{}".format(p.stdout))
        raise Exception("dcm2niix failed: {}".format(p.returncode))

    # Identifying output files
    log_list = p.stdout.split("\n")
    dcm_files = []
    json_file = None
    for l in log_list:
        tag = "DICOM file: "
        if l.startswith(tag):
            dcm_files.append(l[len(tag):])
            continue
        tag = "Converting "
        if l.startswith(tag):
            logger.info(l)
            converting = l[len(tag):]
            dump_path, dump_file  = os.path.split(converting)
            dump_file = "header_dump_" + tools.change_ext(dump_file, "json")
            dump_file = os.path.join(dump_path, dump_file)
            continue

        tag = "Convert "
        if l.startswith(tag):
            logger.info(l)
            res = re.fullmatch("Convert ([0-9]+) DICOM as (.*) "
                               "(\((?:[0-9]+x)+[0-9]+\))", l)
            if os.path.isfile(dump_file):
                out_dump_path, out_dump_file  = os.path.split(res.group(2))
                out_dump_file = "header_dump_" + out_dump_file + ".json"
                out_dump_file = os.path.join(out_dump_path, out_dump_file)

                dcm_json = res.group(2) + ".json"
                if os.path.isfile(dcm_json):
                    with open(dcm_json, "r") as f:
                        js = json.load(f)
                    os.remove(js)
                    with open(dump_file, "r") as f:
                        dump = json.load(f)
                    dump["custom"].update(js)
                    with open(out_dump_file, "w") as f:
                        json.dump(dump, f, indent="  ")
                else:
                    shutil.copyfile2(dump_file, out_dump_file)
            converting = None
            continue

        if l.startswith("Warning: "):
            logger.warning(l)
        elif echo:
            logger.info(l)

    # Removing old dicoms
    if remove:
        for file in dcm_files:
            json_file = "header_dump_" + tools.change_ext(file, "json")
            os.remove(file)
            if os.path.isfile(json_file):
                os.remove(json_file)
