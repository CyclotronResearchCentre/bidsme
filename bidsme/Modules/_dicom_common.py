###############################################################################
# _dicom_common.py provides common functionalities to read and parce DICOM file
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
import pydicom
import re

from dicom_parser.utils.siemens.csa.ascii.ascconv import parse_ascconv

from datetime import datetime

logger = logging.getLogger(__name__)


def isValidDICOM(file: str, mod: list = []) -> bool:
    """
    Returns True if file is valid DICOM file.
    If mod is not empty, checks if Modality tag
    corresponds to given one

    Parameters
    ----------
    file: str
        path to file to read (must exist)
    mod: str, optional
        Modality tag to check

    Returns
    -------
    bool:
        True if file is DICOM with given modality
    """
    with open(file, 'rb') as dcmfile:
        dcmfile.seek(0x80)
        if dcmfile.read(4) != b"DICM":
            logger.debug("Missing DICOM magic string")
            return False
        if not mod:
            return True

        dcmfile.seek(0)
        ds = pydicom.dcmread(dcmfile, specific_tags=["Modality"])
        if "Modality" not in ds:
            logger.warnng('{}: DICOM file misses Modality tag'
                          .format(file))
            return False
        if ds["Modality"].value in mod:
            return True
        else:
            logger.debug("Unaccepted modality: {}"
                         .format(ds["Modality"].value))
            return False
    return False


def retrieveFromDataset(
        path: list, dataset: pydicom.Dataset,
        fail_on_not_found: bool = True,
        fail_on_last_not_found: bool = True,
        ) -> object:
    """
    Search for a tag given in path in dataset, and returns found
    tag value

    Parameters
    ----------
    path: list
        list of strings representing path to searched value
    dataset: pydicom.Dataset
        DICOM dataset to search in
    fail_on_not_found: bool
        if True raises KeyError if given path is not valid,
        returns None elsewere
    fail_on_last_not_found: bool
        same as fail_on_not_found, except for only last element of path

    Returns
    -------
    object:
        retrieved object or None if not found
    """
    res = None
    value = dataset
    count = 0
    try:
        for f in path:
            f = f.strip()
            tag = getTag(f)
            if tag is not None:
                f = tag
            if isinstance(value, pydicom.dataset.Dataset):
                value = value[f]
            elif isinstance(value, pydicom.dataelem.DataElement):
                # Sequence element
                if value.VR == "SQ":
                    value = value[int(f)]
                else:
                    break
            count += 1
        res = DICOMtransform(value)
        for i in range(count, len(path)):
            res = res[int(path[i])]
            count += 1
    except KeyError as e:
        count += 1
        if not fail_on_not_found:
            return None
        if not fail_on_last_not_found and count == len(path):
            return None
        raise KeyError("{}: key error {}"
                       .format(path[0:count], e))
    except IndexError:
        count += 1
        if not fail_on_not_found:
            return None
        if not fail_on_last_not_found and count == len(path):
            return None
        raise KeyError("{}: key error {}"
                       .format(path[0:count], f))
    return res


def getTag(tag: str) -> tuple:
    """
    Parces a DICOM tag from string into a tuple of int

    String is expected to have format '(%4d, %4d)', and
    tag numbers are expected to be in DICOM standart form:
    hex numbers without '0x' prefix

    Parameters
    ----------
    tag: str
        string tag, e.g. '(0008, 0030)'

    Returns
    -------
    (int, int)
    None
    """
    res = re.fullmatch("\\(([0-9a-fA-F]{4})\\, ([0-9a-fA-F]{4})\\)", tag)
    if res:
        return (int(res.group(1), 16), int(res.group(2), 16))
    else:
        return None


def DICOMtransform(element: pydicom.dataelem.DataElement,
                   clean: bool = False):
    if element is None:
        return None
    VR = element.VR
    VM = element.VM
    val = element.value

    try:
        if VR == "OB" and (element.tag == (0x0029, 0x1010)
                           or element.tag == (0x0029, 0x1020)):
            return decodeCSA(val)
        if VM > 1:
            return [decodeValue(val[i], VR, clean) for i in range(VM)]
        else:
            return decodeValue(val, VR, clean)

    except Exception as e:
        logger.warning('Failed to decode tag {} of type {} for: {}'
                       .format(element.name, VR, e))
        return None


def decodeValue(val, VR: str, clean=False):
    """
    Decodes a value from pydicom.DataElement to corresponding
    python class following description in:
    http://dicom.nema.org/medical/dicom/current/output/
    chtml/part05/sect_6.2.html

    Nested values are not permitted

    Parameters
    ----------
    val:
        value as stored in DataElements.value
    VR: str
        Value representation defined by DICOM
    clean: bool
        if True, values of not-basic classes (None, int, float)
        transformed to string

    Returns
    -------
        decoded value
    """

    # Byte Numbers:
    # parced by pydicom, just return value
    if VR in ("FL", "FD",
              "SL", "SS", "SV",
              "UL", "US", "UV"):
        return val

    # Text Numbers
    # using int(), float()
    if VR == "DS":
        if val:
            return float(val)
        else:
            return None
    if VR == "IS":
        if val:
            return int(val)
        else:
            return None

    # Text and text-like
    # using strip to remove apddings
    if VR in ("AE", "CS",
              "LO", "LT",
              "SH", "ST", "UC",
              "UR", "UT", "UI"):
        return val.strip(" \0")

    # Persons Name
    # Use decoded original value
    if VR == "PN":
        if isinstance(val, str):
            return val.strip(" \0")
        if val == "":
            return None

        if len(val.encodings) > 0:
            enc = val.encodings[0]
            return val.original_string.decode(enc)
        else:
            logger.warning("PN: unable to get encoding")
            return ""

    # Age string
    # unit mark is ignored, value converted to int
    if VR == "AS":
        if not val:
            return None
        if val[-1] in "YMWD":
            return int(val[:-1])
        else:
            return int(val)

    # Date and time
    # converted to corresponding datetime subclass
    if VR == "TM":
        if not val:
            return None
        if "." in val:
            dt = datetime.strptime(val, "%H%M%S.%f").time()
        else:
            dt = datetime.strptime(val, "%H%M%S").time()
        if clean:
            return dt.isoformat()
        else:
            return dt
    if VR == "DA":
        if not val:
            return None
        dt = datetime.strptime(val, "%Y%m%d").date()
        if clean:
            return dt.isoformat()
        else:
            return dt
    if VR == "DT":
        if not val:
            return None
        val = val.strip()
        date_string = "%Y%m%d"
        time_string = "%H%M%S"
        ms_string = ""
        uts_string = ""
        if "." in val:
            ms_string += ".%f"
        if "+" in val or "-" in val:
            uts_string += "%z"
        if len(val) == 8 or \
                (len(val) == 13 and uts_string != ""):
            logger.warning("{}: Format is DT, but string looks like DA"
                           .format(val))
            t = datetime.strptime(val, date_string + uts_string)
        elif len(val) == 6 or \
                (len(val) == 13 and ms_string != ""):
            logger.warning("{}: Format is DT, but string looks like TM"
                           .format(val))
            t = datetime.strptime(val, time_string + ms_string)
        else:
            t = datetime.strptime(val, date_string + time_string
                                  + ms_string + uts_string)
        if t.tzinfo is not None:
            t += t.tzinfo.utcoffset(t)
            t = t.replace(tzinfo=None)
        if clean:
            return t.isoformat()
        else:
            return t

    # Invalid type
    # Attributes and sequences will produce warning and return
    # None
    if VR in ("AT", "SQ", "UN"):
        raise ValueError("invalid VR: {}".format(VR))

    # Other type
    # Attempting to decode SV10 formatted bytes string
    # Not clear how parce them
    if VR in ("OB", "OD", "OF", "OL", "OV", "OW"):
        return "{}: {}".format(VR, repr(val))

    # unregistered VR
    raise ValueError("invalid VR: {}".format(VR))


def decodeCSA(val):
    from nibabel.nicom import csareader
    csaheader = dict()
    for tag, item in csareader.read(val)["tags"].items():
        if len(item["items"]) == 0:
            continue

        if tag == "MrPhoenixProtocol" or tag == "MrProtocol":
            csaheader[tag] = parse_ascconv(item["items"][0], '""')[0]
            continue

        if len(item["items"]) == 1:
            csaheader[tag] = item["items"][0]
        else:
            csaheader[tag] = item["items"]

    return csaheader


def extractStruct(dataset: pydicom.dataset.Dataset) -> dict:
    """
    Recurcively extract data from DICOM dataset and put it
    into dictionary. Key are created from keyword, or if not
    defined from tag.

    Values are parced from DataElement values, multiple values
    are stored as list.
    Sequences are stored as lists of dictionaries

    Parameters
    ----------
    dataset: pydicom.dataset.Dataset
        dataset to extract

    Returns
    -------
    dict
    """
    res = dict()

    for el in dataset:
        key = el.keyword
        if key == '':
            key = el.name.replace(" ", "").strip("[]")
            if key == "Unknown":
                key = str(el.tag)
        if el.VR == "SQ":
            res[key] = [extractStruct(val)
                        for val in el]
        else:
            res[key] = DICOMtransform(el, clean=True)
    return res


def combineDateTime(dataset: pydicom.Dataset, timeId: str) -> datetime:
    """
    Retrieves DateTime, Date, Time and combines them

    Parameters
    ----------
    timeId: str
        prefix for DateTime string --  Acquisition, Instance, Content etc...

    Returns
    -------
    datetime, None:
        combined datetime or None if not found
    """
    field = timeId + "DateTime"
    if field in dataset:
        dt_stamp = dataset[field]
        return DICOMtransform(dt_stamp)

    field = timeId + "Date"
    if field in dataset:
        date_stamp = DICOMtransform(dataset[field])
    else:
        return None

    field = timeId + "Time"
    if field in dataset:
        time_stamp = DICOMtransform(dataset[field])
    else:
        return None
    acq = datetime.combine(date_stamp, time_stamp)
    return acq
