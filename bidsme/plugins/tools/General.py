###############################################################################
# General.py contains general tools, that can be used in user plugins
# general tools do not require additional modules installation
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
import math
import logging
import zipfile

logger = logging.getLogger(__name__)


def CheckSeries(path: str,
                expected_series: list,
                strict: bool=True,
                complete: bool=True,
                order: bool=True,
                level: int=logging.ERROR) -> bool:
    """
    Tool for checking the series in the prepared dataset
    to be conformed with passed list. It may be used
    in preparation step in SessionEndEP, or in process/bidsify
    steps in SessioEP.

    Function returns true if all series in given path are in given list.

    Parameters:
    -----------
    path: str
        path to the folder to check, including the data type sub-folder,
        expected to exist
    expected_series: list
        list of expected series Ids (without series number) in expected order
    strict: bool
        if true, check will fail if several series in folder corresponds
        to same series in list
    complete: bool
        if true, fails if not all series in given list found in path
    order: bool
        if true, fails if series in given path are out of order given
        in list, order=True implies strict=True
    level: int
        defines in what logging cathegory error messages will be
        reported (set to logging.NOTSET to silence)

    Example:
    --------
    # In SessionEndEP, given
    #   preparefolder is the path to prepared dataset
    #   session is the BidsSession object passed to SessionEndEP
    #   series is a dictionary with session name as key, and list
    #       of series as values
    path = os.path.join(preparefolder, session.getPath(True), "MRI")
    if not dry_run:
        if not CheckSeries(path, series[session.session]):
            logger.error("{}:{} Series do not match expectation."
            .format(session.subject, session.session))
    """

    if order:
        strict = True

    passed = True
    series = sorted(os.listdir(path))
    series = [s.split("-", 1)[1] for s in series]
    matches = dict.fromkeys(series, -1)

    logger.debug("Found series: {}".format(series))
    logger.debug("Matching against: {}".format(expected_series))

    for ind, s in enumerate(series):
        offset = matches[s] + 1
        if s not in expected_series[offset:]:
            logger.log(level, "Invalid serie [{}] {}".format(ind, s))
            passed = False
            continue

        expected_index = expected_series.index(s, offset)
        if strict:
            matches[s] = expected_index

        if order:
            if ind != expected_index:
                logger.log(level,
                           "Serie [{}] {}, expected at {}"
                           .format(ind, s, expected_index))
                passed = False
                continue

    if complete:
        matches = dict.fromkeys(expected_series, -1)
        for ind, s in enumerate(expected_series):
            if s not in series[matches[s] + 1:]:
                logger.log(level, "Expected series [{}] {} not found"
                           .format(ind, s))
                passed = False
                continue
            matches[s] = series.index(s)

    return passed


def StoreSource(source_path: str, bidsified_path,
                level: str="type", 
                compression=zipfile.ZIP_DEFLATED,
                mode="override"):
    """
    Archive current series into sourcedata folder in the bidsified dataset
    Only files in series folder are archived. It is assumed that working
    directory is structured in standartd way for prepeared dataset.

    Must be run only once within SequenceEP and SequenceEndEP

    Parameters:
    -----------
    source_path: str
        path to folder to archive
    bidsified_path: str
        path to bidsified dataset
    level: str
        folder level in which place the archive
            sourcedata -- in sourcedata(root) directory
            sub -- in subject folders (sourcedata/sub-001)
            ses -- in session folders (sourcedata/sub-001/ses-AAA)
            type -- in data type folder (sourcedata/sub-001/ses-AAA/MRI)
    compression: int
        numerical constant indicating algorythm to use, from fastest
        to more performing:
            zipfile.ZIP_STORED -- uncompressed
            zipfile.ZIP_DEFLATED -- standard zip
            zipfile.ZIP_BZIP2 -- bzip
            zipfile.ZIP_LZMA -- lzma
    mode: str
        mode to use then archive already exists, one of the next:
            error -- raise FileExistsError
            override -- replace archive
            append -- append files to existing archive
            increment -- add a counter to extention, up to 20

    Example:
    --------
    # In SequenceEP, given
    #   recording is BaseModule object
    #   bidsified is the path to bidsified dataset
    if not dry_run:
        StoreSource(recording.recPath(), bidsified)
    """
    if level == "sourcedata":
        level = 0
    elif level == "sub":
        level = 1
    elif level == "ses":
        level = 2
    elif level == "type":
        level = 3
    else:
        raise ValueError("Unknown level for archiving: {}"
                         .format(level))

    path = os.path.normpath(source_path)
    # path, series = os.path.split(path)
    path, archive = os.path.split(path)
    out_path = [None] * (level)
    for i in range(level - 1, -1, -1):
        path, out_path[i] = os.path.split(path)

    out_path = os.path.join(bidsified_path, "sourcedata", *out_path)
    os.makedirs(out_path, exist_ok=True)

    out_name = os.path.join(out_path, archive + '.zip')
    m = "w"
    if os.path.isfile(out_name):
        if mode == "error":
            raise FileExistsError("Archive {} already exists"
                                  .format(out_name))
        elif mode == "append":
            m = "a"
        elif mode == "increment":
            found = False
            for count in range(21):
                out_name = os.path.join(out_path,
                                        "{}.{}.zip".format(archive, count))
                if not os.path.isfile(out_name):
                    found = True
                    break
            if not found:
                raise FileExistsError("Archive {} already exists"
                                      .format(out_name))
        elif mode != "override":
            raise ValueError("Unknown mode: {}".format(mode))

    zip_file = zipfile.ZipFile(out_name, m, compression)

    path_sep = source_path + os.path.sep
    for root, directories, files in os.walk(path_sep):
        root_trunc = root[len(path_sep):]
        for directory in directories:
            zip_file.write(os.path.join(root, directory),
                           os.path.join(root_trunc, directory))
        for file in files:
            zip_file.write(os.path.join(root, file),
                           os.path.join(root_trunc, file))
    zip_file.close()


def ExtractBval(recording):
    """
    Extracts Bval and Bvec values from a DWI recording
    Might work only on Siemens files

    Parameters:
    -----------
    recording: Modules.baseModule
        recording from which extract values

    Returns:
    --------
    (float, [float, float, float])
        (bval, [bvec_x, bvec_y, bvec_z])

    Example:
    --------
    # In FileEP, given
    #   recording is BaseModule object
    #   bval is a list for b-values,
    #   bvec_x, bvec_y, bvec_z are lists for b-vector composantes x,y,z
    if mod == "dwi":
        val, vec = ExtractBval(recording)
        bval.append(val)
        bvec_x.append(vec[0])
        bvec_y.append(vec[1])
        bvec_z.append(vec[2])
    """
    bval = recording.getField("CSAImageHeaderInfo/B_value", default=0)
    bvec = recording.getField("CSAImageHeaderInfo/DiffusionGradientDirection",
                              default=[0, 0, 0])
    norm = math.sqrt(sum(x**2 for x in bvec))
    if norm > 0:
        bvec = [bvec[0] / norm, -bvec[1] / norm, -bvec[2] / norm]
    return bval, bvec


def SaveBval(fname: str,
             bval: list,
             bvec_x: list, bvec_y: list, bvec_z: list,
             precision: int=4):
    """
    Saves b-values and vector given in bval, bvec_x, y, z
    parameters into file derived from fname by changing extension.

    Parameters:
    -----------
    fname: str
        name of current recording file in destination directory
    bval: list(float)
        list of b-values
    bvec_x: list(float)
        list of x components of b-vector
    bvec_y: list(float)
        list of y components of b-vector
    bvec_z: list(float)
        list of z components of b-vector

    Raises:
    -------
    IndexError:
        if lenghts of passed lists mismatches

    Example:
    --------
    # In SequenceEndEP, given
    #   recording is BaseModule object
    #   bval is a list for b-values,
    #   bvec_x, bvec_y, bvec_z are lists for b-vector composantes x,y,z
    if mod == "dwi":
        val, vec = ExtractBval(recording)
        bval.append(val)
        bvec_x.append(vec[0])
        bvec_y.append(vec[1])
        bvec_z.append(vec[2])
    """
    out_base = os.path.splitext(fname)[0]

    size = len(bval)
    if size != len(bvec_x) or size != len(bvec_y) or size != len(bvec_z):
        raise IndexError("Bval vector mismach size with Bvec")

    f_bval = open(out_base + ".bval", "w")
    f_bvec = open(out_base + ".bvec", "w")
    float_format = "{:." + str(precision) + "f}"

    for val in bval[:-1]:
        f_bval.write(float_format.format(val) + " ")
    f_bval.write(float_format.format(bval[-1]) + "\n")

    for vec in (bvec_x, bvec_y, bvec_z):
        for val in vec[:-1]:
            f_bvec.write(float_format.format(val) + " ")
        f_bvec.write(float_format.format(vec[-1]) + "\n")

    f_bval.close()
    f_bvec.close()
