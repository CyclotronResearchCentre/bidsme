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
import dcm2niix

from bidsme.tools import tools
from bidsme.Modules import baseModule

logger = logging.getLogger(__name__)


def convert(outfolder: str, recording: baseModule, use_dump=True):
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
    # Creating a list of files in case if not all files
    # in recording are in output folder
    flist = [f for f in os.listdir(outfolder)
             if f in recording.files
             ]
    flist.sort()

    if use_dump:
        out_files = []
        for i, f in enumerate(flist):
            json_file = "header_dump_" + tools.change_ext(f, "json")
            with open(os.path.join(outfolder, json_file)) as fjs:
                js = json.load(fjs)
            basename = "{}_{:06d}".format(js["recId"], i)
            shutil.move(os.path.join(outfolder, f),
                        os.path.join(outfolder, basename + ".IMA"))
            shutil.move(os.path.join(outfolder, json_file),
                        os.path.join(outfolder,
                                     "header_dump_" + basename + ".json"))
            out_files.append(basename + ".IMA")
    else:
        out_files = flist

    logger.info("Converting {} images".format(len(flist)))

    # Building up dcm2niix parameters
    params = []
    dcm2niix_options = {"-a": "y", "-d": "1", "-z": "o",
                        "-w": "0"}
    if use_dump:
        dcm2niix_options["-f"] = "%b"
        dcm2niix_options["--terse"] = None

    for key, val in dcm2niix_options.items():
        params.append(key)
        if val is not None:
            params.append(val)
    params.append(outfolder)
    dcm2niix.main(params)

    # Removing original files
    for fname in out_files:
        json_file = "header_dump_" + tools.change_ext(fname, "json")
        os.remove(os.path.join(outfolder, fname))
        candidate = fname + ".nii.gz"
        if os.path.isfile(os.path.join(outfolder, candidate)):
            # Merge metadata
            js = tools.change_ext(candidate, "json")
            with open(os.path.join(outfolder, js)) as fjs:
                js_ext = json.load(fjs)
            os.remove(os.path.join(outfolder, js))

            with open(os.path.join(outfolder, json_file)) as fjs:
                js_source = json.load(fjs)
            js_ext.update(js_source["custom"])
            js_source["custom"] = js_ext

            ext_name = "header_dump_{}".format(js)
            with open(os.path.join(outfolder, ext_name), "w") as fjs:
                json.dump(js_source, fjs, indent="  ")

        os.remove(os.path.join(outfolder, json_file))
