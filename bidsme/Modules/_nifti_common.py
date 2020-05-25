###############################################################################
# _nifti_common.py provides common functionalities to read and parce NIFTI file
###############################################################################
# Copyright (c) 2019-2020, University of Liège
# Author: Nikita Beliy
# Owner: Liege University https://www.uliege.be
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

import logging
import struct


logger = logging.getLogger(__name__)


def isValidNIFTI(file: str) -> bool:
    """
    Returns True if given file is valid, i.e.
    first 4 bites are 348 or 540 and magic string
    is one of "ni1", "n+1" or "n+2"

    Parameters
    ----------
    file: str
        path to file (must exist)
    """
    with open(file, 'rb') as niifile:
        d = niifile.read(4)
        if len(d) != 4:
            return False

        hdr = struct.unpack("<i", d)[0]
        # Nifti 1
        if hdr in (348, 1543569408):
            niifile.seek(344, 0)
            magic = niifile.read(4)
        # Nifti 2
        elif hdr in (540, 469893120):
            niifile.seek(4, 0)
            magic = niifile.read(4)
        else:
            return False
        if magic in (b'ni1\x00', b'n+1\x00', b'n+2\x00'):
            return True
        return False


def getEndType(path: str) -> tuple:
    """
    Returns endiannes symbol '>' or '<' and type
    'ni1', 'n+1', 'n+2' of nifti file

    Parameters
    ----------
    path: str
        path to nifti header file

    Returns
    -------
    (str, str):
        tuple of endianess symbol and nifti type
    """
    with open(path, "rb") as niifile:
        header_size = struct.unpack("<i", niifile.read(4))[0]
        if header_size in (348, 540):
            endian = "<"
        else:
            endian = ">"

        if header_size in (348, 1543569408):
            if path.endswith(".hdr"):
                ftype = "ni1"
            else:
                ftype = "n+1"
            niifile.seek(40, 0)
            dim_0 = struct.unpack(endian + "h", niifile.read(2))[0]
            niifile.seek(344, 0)
            magic = niifile.read(4).decode().strip("\x00")
        else:
            ftype = "n+2"
            if path.endswith(".hdr"):
                logger.error("NIFTI: {} .hdr/.img cannot be NIFTI-2"
                             .format(path))
                raise Exception("Corrupted file {}".format(path))
            niifile.seek(16, 0)
            dim_0 = struct.unpack(endian + "q", niifile.read(8))[0]
            niifile.seek(4, 0)
            magic = niifile.read(8).decode().strip("\x00")

        # confirming endianness and magic string
        if dim_0 < 1 or dim_0 > 7:
            logger.critical("NIFTI:{} corrupted file -- "
                            "conflicting endiannes"
                            .format(path))
            raise Exception("Corrupted file {}".format(path))
        if magic != ftype:
            logger.critical("NIFTI:{} corrupted file -- "
                            "conflicting format version"
                            .format(path))
            raise Exception("Corrupted file {}".format(path))

        return endian, ftype


def parceNIFTIheader_1(path: str, endian: str) -> dict:
    """
    Parces NIFTI1 header and returns resulting dictionary

    Parameters
    ----------
    path: str
        path to nifti1 file
    endian: str
        endiannes symbol as defined by struct package

    Returns
    -------
    dict:
        parced header
    """
    res = dict()
    with open(path, "rb") as niifile:
        header = niifile.read(348)

    res["diminfo"] = struct.unpack("c", header[39:40])[0]
    res["dim"] = struct.unpack(endian + "8h", header[40:56])
    res["intent_p1"] = struct.unpack(endian + "f", header[56:60])[0]
    res["intent_p2"] = struct.unpack(endian + "f", header[60:64])[0]
    res["intent_p3"] = struct.unpack(endian + "f", header[64:68])[0]
    res["intent_code"] = struct.unpack(endian + "h", header[68:70])[0]
    res["datatype"] = struct.unpack(endian + "h", header[70:72])[0]
    res["bitpix"] = struct.unpack(endian + "h", header[72:74])[0]
    res["slice_start"] = struct.unpack(endian + "h", header[74:76])[0]
    res["pixdim"] = struct.unpack(endian + "8f", header[76:108])
    res["vox_offset"] = struct.unpack(endian + "f", header[108:112])[0]
    res["scl_slope"] = struct.unpack(endian + "f", header[112:116])[0]
    res["scl_inter"] = struct.unpack(endian + "f", header[116:120])[0]
    res["slice_end"] = struct.unpack(endian + "h", header[120:122])[0]
    res["slice_code"] = struct.unpack(endian + "b", header[122:123])[0]
    res["xyz_units"] = struct.unpack(endian + "b", header[123:124])[0]
    res["cal_max"] = struct.unpack(endian + "f", header[124:128])[0]
    res["cal_min"] = struct.unpack(endian + "f", header[128:132])[0]
    res["slice_duration"] = struct.unpack(endian + "f", header[132:136])[0]
    res["toffset"] = struct.unpack(endian + "f", header[136:140])[0]
    res["glmax"] = struct.unpack(endian + "i", header[140:144])[0]
    res["glmin"] = struct.unpack(endian + "i", header[144:148])[0]
    res["descrip"] = header[148:228].decode().strip("\0 ")
    res["aux_file"] = header[228:252].decode().strip("\0 ")
    res["qform_code"] = struct.unpack(endian + "h", header[252:254])[0]
    res["sform_code"] = struct.unpack(endian + "h", header[254:256])[0]
    res["quatern_b"] = struct.unpack(endian + "f", header[256:260])[0]
    res["quatern_c"] = struct.unpack(endian + "f", header[260:264])[0]
    res["quatern_d"] = struct.unpack(endian + "f", header[264:268])[0]
    res["qoffset_x"] = struct.unpack(endian + "f", header[268:272])[0]
    res["qoffset_y"] = struct.unpack(endian + "f", header[272:276])[0]
    res["qoffset_z"] = struct.unpack(endian + "f", header[276:280])[0]
    res["srow_x"] = struct.unpack(endian + "4f", header[280:296])
    res["srow_y"] = struct.unpack(endian + "4f", header[296:312])
    res["srow_z"] = struct.unpack(endian + "4f", header[312:328])
    res["intent_name"] = header[328:344].decode().strip("\0 ")

    return res


def parceNIFTIheader_2(path: str, endian: str) -> dict:
    """
    Parces NIFTI2 header and returns resulting dictionary

    Parameters
    ----------
    path: str
        path to nifti2 file
    endian: str
        endiannes symbol as defined by struct package

    Returns
    -------
    dict:
        parced header
    """
    res = dict()
    with open(path, "rb") as niifile:
        header = niifile.read(540)

    res["datatype"] = struct.unpack(endian + "h", header[12:14])[0]
    res["bitpix"] = struct.unpack(endian + "h", header[14:16])[0]
    res["dim"] = struct.unpack(endian + "8q", header[16:80])
    res["intent_p1"] = struct.unpack(endian + "d", header[80:88])[0]
    res["intent_p2"] = struct.unpack(endian + "d", header[88:96])[0]
    res["intent_p3"] = struct.unpack(endian + "d", header[96:104])[0]
    res["pixdim"] = struct.unpack(endian + "8d", header[104:168])
    res["vox_offset"] = struct.unpack(endian + "q", header[168:176])[0]
    res["scl_slope"] = struct.unpack(endian + "d", header[176:184])[0]
    res["scl_inter"] = struct.unpack(endian + "d", header[184:192])[0]
    res["cal_max"] = struct.unpack(endian + "d", header[192:200])[0]
    res["cal_min"] = struct.unpack(endian + "d", header[200:208])[0]
    res["slice_duration"] = struct.unpack(endian + "d", header[208:216])[0]
    res["toffset"] = struct.unpack(endian + "d", header[216:224])[0]
    res["slice_start"] = struct.unpack(endian + "q", header[224:232])[0]
    res["slice_end"] = struct.unpack(endian + "q", header[232:240])[0]
    res["descrip"] = header[240:320].decode().strip("\0 ")
    res["aux_file"] = header[320:344].decode().strip("\0 ")
    res["qform_code"] = struct.unpack(endian + "i", header[344:348])[0]
    res["sform_code"] = struct.unpack(endian + "i", header[348:352])[0]
    res["quatern_b"] = struct.unpack(endian + "d", header[352:360])[0]
    res["quatern_c"] = struct.unpack(endian + "d", header[360:368])[0]
    res["quatern_d"] = struct.unpack(endian + "d", header[368:376])[0]
    res["qoffset_x"] = struct.unpack(endian + "d", header[376:384])[0]
    res["qoffset_y"] = struct.unpack(endian + "d", header[384:392])[0]
    res["qoffset_z"] = struct.unpack(endian + "d", header[392:400])[0]
    res["srow_x"] = struct.unpack(endian + "4d", header[400:432])
    res["srow_y"] = struct.unpack(endian + "4d", header[432:464])
    res["srow_z"] = struct.unpack(endian + "4d", header[464:496])
    res["slice_code"] = struct.unpack(endian + "i", header[496:500])[0]
    res["xyz_units"] = struct.unpack(endian + "i", header[500:504])[0]
    res["intent_code"] = struct.unpack(endian + "i", header[504:508])[0]
    res["intent_name"] = header[508:524].decode().strip("\0 ")

    return res
