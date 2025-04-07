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

logger = logging.getLogger(__name__)


def convert(dcm_folder: str, binary=None, echo=False, remove=True,
            params={}):
    """
    Use dcm2niix (https://github.com/rordenlab/dcm2niix)
    to convert DICOM files to NIFTY with default options
    -a y -f %p_%s -i y -z y
    These options can be changed by providing params dictionary.

    If original DICOM files are acompagnied by bidsme header file,
    the metadata exported by dcm2niix will be incorporated in to
    the header file as custom fields, and will be automatically
    used during bidsification.

    If echo is true, the output od dcm2niix will bi redirected
    to logger (the output will be verbose!).

    If remove is true, the DCM files detected by dcm2niix will
    be removed, be carefull to run this function outside prepared
    dataset!

    This tool is intended to be used in preparation step
    in SequenceEndEP.

    Parameters:
    -----------
    dcm_folder: str
        path to output folder where data files has been copied
    binary: str | None
        path to the dcm2niix executable, if None, the default
        system executable will be used
    echo: bool
        If True, all dcm2niix output will be redirected to
        logger (the verbosity is fixed to 1).
        If False (default), only basic information will be given
        to logger.
    remove: bool
        If True (default), the original DICOM files will be removed.
        If False, the original files will be conserved, this can
        interfere with future bidsification step.
    params: dict
        dictionary of parameters to be passed to dcm2niix.
        The verbosity (-v) will be fixed to verbose(1).
        For repeated arguments (-n) provide a list of values.
        For switches (--ignore_trigger_times) provide None.
        If the -o is not specified, the input folder will be
        used.

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
        dcm2niix.convert(outfolder, {"-i": "y", "-f", "%p_%r"})
    """
    # Testing dcm2niix executable
    if not binary:
        binary = dcm2niix.bin
    try:
        p = run([binary] + ["--version"], capture_output=True, text=True)
    except FileNotFoundError:
        logger.error("Can't find dcm2niix executable at {}".format(binary))
        raise
    logger.info(p.stdout.split("\n")[0])

    # Building up dcm2niix parameters
    dcm_params = {"-a": "y",
                  "-f": "%p_%s",
                  "-i": "y",
                  "-z": "y"}
    dcm_params.update(params)
    dcm_params["-v"] = 1
    dcm2niix_options = [binary]
    for arg, val in dcm_params.items():
        if isinstance(val, list):
            for subval in val:
                dcm2niix_options.append(arg)
                dcm2niix_options.append(str(val))
        else:
            dcm2niix_options.append(arg)
            if val is not None:
                dcm2niix_options.append(str(val))
    dcm2niix_options.append(dcm_folder)

    # Running conversion
    logger.info('"' + '" "'.join(dcm2niix_options) + '"')
    p = run(dcm2niix_options, capture_output=True, text=True)
    if p.returncode == 2 and p.stderr.strip() == "":
        logger.error("dcm2niix failed with error code {}".format(p.returncode))
        logger.error("Unable to find any DICOM images in {}"
                     .format(dcm_folder.strip()))
        logger.info("stdout: {}".format(p.stdout.strip()))
        raise Exception("dcm2niix failed: {}".format(p.returncode))

    if p.returncode != 0:
        logger.error("dcm2niix failed with error code {}".format(p.returncode))
        logger.error("stderr: {}".format(p.stderr.strip()))
        logger.info("stdout: {}".format(p.stdout.strip()))
        raise Exception("dcm2niix failed: {}".format(p.returncode))

    # Identifying output files
    log_list = p.stdout.split("\n")
    dcm_files = []
    for ln in log_list:
        tag = "DICOM file: "
        if ln.startswith(tag):
            dcm_files.append(ln[len(tag):])
            continue
        tag = "Converting "
        if ln.startswith(tag):
            logger.info(ln)
            converting = ln[len(tag):]
            dump_path, dump_file = os.path.split(converting)
            dump_file = "header_dump_" + tools.change_ext(dump_file, "json")
            dump_file = os.path.join(dump_path, dump_file)
            continue

        tag = "Convert "
        if ln.startswith(tag):
            logger.info(ln)
            res = re.fullmatch(r"Convert ([0-9]+) DICOM as (.*) "
                               r"(\((?:[0-9]+x)+[0-9]+\))", ln)
            if os.path.isfile(dump_file):
                out_dump_path, out_dump_file = os.path.split(res.group(2))
                out_dump_file = "header_dump_" + out_dump_file + ".json"
                out_dump_file = os.path.join(out_dump_path, out_dump_file)

                dcm_json = res.group(2) + ".json"
                if os.path.isfile(dcm_json):
                    with open(dcm_json, "r") as f:
                        js = json.load(f)
                    os.remove(dcm_json)
                    with open(dump_file, "r") as f:
                        dump = json.load(f)
                    js.update(dump["custom"])
                    dump["custom"] = js
                    with open(out_dump_file, "w") as f:
                        json.dump(dump, f, indent="  ")
                else:
                    shutil.copyfile2(dump_file, out_dump_file)
            converting = None
            continue

        if ln.startswith("Warning: "):
            logger.warning(ln)
        elif echo:
            logger.info(ln)

    # Removing old dicoms
    if remove:
        logger.info("Removing {} DCM files".format(len(dcm_files)))
        for file in dcm_files:
            dump_path, dump_file = os.path.split(file)
            dump_file = "header_dump_" + tools.change_ext(dump_file, "json")
            os.remove(file)
            try:
                os.remove(os.path.join(dump_path, dump_file))
            except FileNotFoundError:
                pass
