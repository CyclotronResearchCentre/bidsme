###############################################################################
# base.py provide the base class for recording, all modules must inherit from
# this base class
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
import shutil
import logging
import json
import re
import numpy
import gzip
import glob

from datetime import datetime, date, time
from collections import OrderedDict
from copy import deepcopy

from .abstract import abstract
from bidsme.tools import tools
from bidsme.bidsMeta import BIDSfieldLibrary
from bidsme.bidsMeta import BidsSession
from bidsme.schema.BIDSschema import BIDSschema

from ._constants import ignoremodality, unknownmodality
from .common import action_value
from .exceptions import CharacteristicError

logger = logging.getLogger(__name__)


class baseModule(abstract):
    """
    Base class from which all modules should inherit
    """
    __slots__ = [
                 # bids name values
                 "_modality",
                 "_bidsSession",
                 "labels",
                 "suffix",
                 # recording attributes
                 "attributes",
                 # user-defined attributes
                 "custom",
                 # local file variables
                 "index",
                 "files",
                 "_recPath",
                 # series identifier
                 "_series_id",
                 "_series_no",
                 # BIDS schema
                 "schema",
                 # json meta variables
                 "metaAuxiliary",
                 "meta_shorcut",
                 # tsv meta variables
                 "rec_BIDSvalues",
                 "sub_BIDSvalues",
                 # general attributes
                 "_acqTime",
                 "manufacturer",
                 "encoding",
                 # dictionary of switches regulating file processing
                 "switches"
                 ]

    _module = "base"
    _type = "None"

    # Name of modality as defined in BIDS schema
    _schema_mod = None
    # List of associated data-types, as defined in BIDS schema
    _schema_data_types = []

    # list of valid file extentions
    _file_extentions = list()

    rec_BIDSfields = BIDSfieldLibrary()
    rec_BIDSfields.AddField(
        name="filename",
        longName="File Name",
        description="Path to the scan file")
    rec_BIDSfields.AddField(
        name="acq_time",
        longName="Acquisition time",
        description="Time corresponding to the first data "
        "taken during the scan")

    sub_BIDSfields = BIDSfieldLibrary()
    sub_BIDSfields.AddField(
            name="participant_id",
            longName="Participant Id",
            description="label identifying a particular subject")
    sub_BIDSfields.AddField(
        name="age",
        longName="Age",
        description="Age of a subject",
        units="year")
    sub_BIDSfields.AddField(
        name="sex",
        longName="Sex",
        description="Sex of a subject",
        levels={
            "F": "Female",
            "M": "Male"}
            )

    def __init__(self):
        """
        Basic class for module. Isn't intended to be
        initiated directly.
        """
        self.files = list()
        self._recPath = ""
        self.index = -1
        self._series_id = None
        self._series_no = None
        self.attributes = dict()
        self.custom = dict()
        self.labels = OrderedDict()
        self.suffix = ""
        self._modality = unknownmodality
        self._bidsSession = None

        self.schema = BIDSschema(self._schema_mod)
        self.meta_shorcut = dict()
        self.metaAuxiliary = dict()
        self.rec_BIDSvalues = self.rec_BIDSfields.GetTemplate()
        self.sub_BIDSvalues = self.sub_BIDSfields.GetTemplate()

        self._acqTime = None
        self.manufacturer = None
        self.encoding = "ascii"

        self.switches = {"exportHeader": False,
                         "zipFile": False}

    #############################
    # Optional virtual methodes #
    #############################
    def clearCache(self) -> None:
        """
        Virtual function that clears cache of current file
        """
        pass

    def _copy_bidsified(self, directory: str, bidsname: str, ext: str) -> None:
        """
        Virtual function that copies bidsified data files to
        its destinattion.

        Parameters
        ----------
        directory: str
            destination directory where files should be copies,
            including modality folder. Assured to exists.
        bidsname: str
            bidsified name without extention
        ext: str
            extention of the data file
        """

        out_fname = os.path.join(directory, bidsname + ext)
        if self.switches["zipFile"] and\
                not self.currentFile().endswith(".gz"):
            with open(self.currentFile(), 'rb') as f_in:
                with gzip.open(out_fname, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
        else:
            shutil.copy2(self.currentFile(), out_fname)

    def _post_copy_bidsified(self,
                             directory: str,
                             bidsname: str,
                             ext: str) -> None:
        """
        Virtual function that performs all post-copy tasks, for ex.
        copy needed auxiliary files or change some internal values
        on copied file. It uses same parameters as _copy_bidsified
        and is executed just after it.

        Parameters:
        -----------
        directory: str
            destination directory where files should be copies,
            including modality folder. Assured to exists.
        bidsname: str
            bidsified name without extention
        ext: str
            extention of the data file
        """
        pass

    def copyRawFile(self, destination: str) -> str:
        """
        Virtual function to Copy raw (non-bidsified) file
        to destination.
        Destination is an existing writable directory

        Parameters
        ----------
        destination: str
            output folder to copied files

        Returns
        -------
        str:
            path to copied file
        """
        if os.path.isfile(os.path.join(destination,
                                       self.currentFile(True))):
            logger.warning("{}: File {} exists at destination"
                           .format(self.recIdentity(),
                                   self.currentFile(True)))
        basename = tools.change_ext(self.currentFile(True), "*")
        to_copy = glob.glob(os.path.join(self._recPath, basename))
        for file in to_copy:
            shutil.copy2(file, destination)
        return os.path.join(destination, self.currentFile(True))

    def exportHeader(self, destination: str) -> None:
        """
        Export image file header to "header_dump_<filename>.json"

        Exported file contain full image header togever with some
        bidsme variables

        Parameters:
        -----------
        destination: str
            output folder where header will be placed
        """

        data_file = self.currentFile(True)
        json_file = "header_dump_" + tools.change_ext(data_file, "json")
        with open(os.path.join(destination, json_file), "w") as f:
            d = dict()
            d["format"] = self.formatIdentity()
            d["manufacturer"] = self.manufacturer
            d["acqDateTime"] = self.acqTime()
            d["subId"] = self._getSubId()
            d["sesId"] = self._getSesId()
            d["recNo"] = self.recNo()
            d["recId"] = self.recId()
            d["custom"] = self.custom
            d["header"] = self.dump()
            json.dump(d, f, indent=2, cls=ExtendEncoder)

    def _transformField(self, value, prefix: str):
        """
        Virtual function to apply custom, format
        depended transformation to retrieved meta data,
        for ex. units conversion.
        Value is garanteed to not be list or dictionary
        or None

        Parameters
        ----------
        value:
            value to transform
        prefix:
            identification of transformation
        """
        try:
            return action_value(value, prefix)
        except Exception as e:
            logger.error("{}: Invalid field prefix {}: {}"
                         .format(self.formatIdentity(),
                                 prefix, e))
            raise

    ##################
    # Class methodes #
    ##################
    @classmethod
    def isValidFile(cls, file: str) -> bool:
        """
        Checks if given file is valid

        Parameters
        ----------
        file: str
            path to file

        Returns
        -------
        bool:
            True if file is valid

        Raises
        ------
        FileNotFoundError
            If path is not a file
        """
        # logger.debug("{}: Testing file {}"
        #              .format(cls.formatIdentity(), file))

        if not os.path.exists(file):
            raise FileNotFoundError("File {} not found or not a file"
                                    .format(file))
        if not os.access(file, os.R_OK):
            raise PermissionError("File {} not readable"
                                  .format(file))
        if os.path.basename(file).startswith('.'):
            logger.debug('{}: Hidden file'
                         .format(cls.formatIdentity()))
            return False

        if cls._file_extentions:
            passed = False
            for ext in cls._file_extentions:
                if file.endswith(ext):
                    passed = True
                    break
            if not passed:
                # logger.debug("{}: Unaccepted extention"
                #              .format(cls.formatIdentity()))
                return False
        try:
            res = cls._isValidFile(file)
            # if res:
            #     logger.debug("{}: Passed"
            #                  .format(cls.formatIdentity()))
            # else:
            #     logger.debug("{}: Rejected"
            #                  .format(cls.formatIdentity()))
            return res

        except Exception:
            # logger.debug("{}: {}"
            #              .format(cls.formatIdentity(), e))
            return False

    @classmethod
    def Module(cls):
        """
        returns Module name of current class
        """
        return cls._module

    @classmethod
    def Type(cls):
        """
        returns file type of current class
        """
        return cls._type

    @classmethod
    def formatIdentity(cls):
        """
        Returns identification string for current type
        in form {Module}/{Type}

        Returns
        -------
        str
        """
        return "{}/{}".format(cls.Module(), cls.Type())

    @classmethod
    def isValidRecording(cls, rec_path: str) -> bool:
        """
        Checks for all files in given directory and returns true if
        found at list one valid file

        Parameters
        ----------
        rec_path: str
            path to directory to check
        Returns
        -------
        bool:
            True if at least one valid file found
        """
        for file in os.listdir(rec_path):
            if cls.isValidFile(os.path.join(rec_path, file)):
                return True
        return False

    @classmethod
    def getNumFiles(cls, folder: str) -> int:
        """
        Returns number of valid files in given folder.
        Files are not loaded

        Parameters
        ----------
        folder: str
            path to folder to scan, must exists

        Returns
        -------
        int:
            number of valid recordings
        """
        count = 0
        for file in os.listdir(folder):
            if os.path.basename(file).startswith('.'):
                logger.warning(f'Ignoring hidden file: {file}')
                continue
            full_path = os.path.join(folder, file)
            if cls.isValidFile(full_path):
                count += 1
        return count

    @classmethod
    def getValidFile(self, folder: str, index: int = 0) -> int:
        """
        Return valid file name of index from given folder without
        loading it.
        Use setRecPath if you want to load valid files.

        Parameters
        ----------
        folder: str
            path to folder to scan, must exists
        index: int
            Index of file to retrieve

        Returns
        -------
        str:
            path to file
        """
        idx = 0
        for file in sorted(os.listdir(folder)):
            if os.path.basename(file).startswith('.'):
                logger.warning(f'Ignoring hidden file: {file}')
                continue

            full_path = os.path.join(folder, file)
            if self.isValidFile(full_path):
                if idx == index:
                    return full_path
                else:
                    idx += 1
        logger.warning("{}/{}: Cant find a valid file at index {} in {}"
                       .format(self.Module(), self.Type(),
                               index, folder))
        return None

    @classmethod
    def isValidModality(cls, modality: str,
                        include_ignored: bool = True) -> bool:
        """
        Returns True if given modality is in in the list
        of declared modalities and False otherwise.

        Parameters
        ----------
        modality: str
            modality name to check
        include_ignored: bool
            switch to include or not the ignored modality

        Returns
        -------
        bool
        """
        passed = False
        if include_ignored and modality == ignoremodality:
            passed = True
        if modality in cls._schema_data_types:
            passed = True
        return passed

    ##################
    # Acess methodes #
    ##################

    def Modality(self):
        """
        Returns current modality
        """
        return self._modality

    def getField(self, field: str, default=None, prefix=':', separator='/'):
        """
        Returns meta value corresponding to a given field.
        A prefix can be used to call a specific transformation
        within a subclass

        Parameters
        ----------
        field: str
            name of the field to retrieve
        default:
            returned value if field not found
        prefix: str
            separater used to identify prefix
        separator: str
            character used to separate levels in case
            of nested fields

        Returns
        -------
        retrieved value or default
        """
        fields = field.split(prefix)
        actions = fields[0:-1]
        field = fields[-1]

        result = self._getField(field.split(separator))

        if result is None:
            if default is None:
                return None
            result = default

        for prefix in reversed(actions):
            if isinstance(result, list):
                result = [self._transformField(v, prefix) for v in result]
            elif isinstance(result, dict):
                result = {k: self._transformField(v, prefix)
                          for k, v in result.items()}
            else:
                result = self._transformField(result, prefix)
        if isinstance(result, str):
            result = result.strip()
        return result

    def getAttribute(self, attribute: str,
                     default=None):
        """
        Returns attribute (field from metadata).
        The main difference between this and getField
        is getAttribute first tries to retrieve value
        from saved attributes, and if it fails, retrieves
        from metadata.
        Retrieved values are stored in memory.

        Parameters
        ----------
        attribute: str
            name of attribute to retrieve
        default:
            value returned in case of field not found
        cleanup: bool
            performs value cleanup, removing any non ASCII
            and non alphanumeric characters. Applied only
            to strings
        raw: bool
            if True, the type of value is conserved.
            if False, value converted to string

        Returns
        -------
        retrieved value
        """
        if attribute in self.attributes:
            return self.attributes[attribute]
        else:
            res = self.getField(attribute, default)
            self.attributes[attribute] = res
            return res

    def setAttribute(self, attribute: str, value):
        self.attributes[attribute] = value

    def resetAttribute(self, attribute):
        self.attributes.pop(attribute)

    def _tag_replacement(self, matchobject, log_lvl,
                         default=None, raw=False):
        if matchobject.group("meta"):
            result = self.getAttribute(matchobject.group("meta"), default)
            if result is None:
                logger.log(log_lvl, "{}: Can't get attribute '{}' from '{}'"
                           .format(self.recIdentity(),
                                   matchobject.group("meta"),
                                   matchobject.string))
                if not raw:
                    result = "<{}>".format(matchobject.group("meta"))
        else:
            result = self.getCharecteristic(matchobject.group("internal"))
        if raw:
            return result
        else:
            return str(result)

    def getDynamicField(self, field: str,
                        default: object = None,
                        cleanup: bool = True, raw: bool = False,
                        warning: bool = True):
        """
        Dynamically retrieves metadata field from recording

        Parameters
        ----------
        field: str
            name of field to retrieve
        default: object
            default value if unable to get field
        cleanup: bool
            if True the result will be transformed
            to be bids-compatible
        raw: bool
            if False, a str(value) will be returned
        warning: bool
            if True, missing attributes will be reported as warning
        """
        if warning:
            log_lvl = logging.WARNING
        else:
            log_lvl = logging.DEBUG

        if not isinstance(field, str) or field == "":
            return field

        expr = re.compile("<<(?P<internal>.*?)>>|<(?P<meta>.*?)>")

        try:
            if raw:
                res = re.fullmatch(expr, field)
                if res:
                    return self._tag_replacement(res, log_lvl, default, True)

            # Results parced into string
            res = re.sub(expr,
                         lambda x: self._tag_replacement(x, log_lvl,
                                                         default, False),
                         field)
        except Exception as err:
            logger.error("{}: Error in dynamic field '{}': {}: {}"
                         .format(self.recIdentity(),
                                 field, type(err).__name__, err))
            raise

        if cleanup:
            res = tools.cleanup_value(res)
        return res

    def setBidsSession(self, session: BidsSession) -> None:
        """
        Set session class
        """
        if self._bidsSession is not None:
            logger.warning("{}: Resetting BidsSession"
                           .format(self.recIdentity()))
        self._bidsSession = BidsSession(session.subject, session.session)
        self._bidsSession.in_path = session.in_path
        self._bidsSession.sub_values = {key: val
                                        for key, val
                                        in session.sub_values.items()}
        self.setSubId()
        self.setSesId()

    def getBidsSession(self):
        return self._bidsSession

    def subId(self):
        """
        Returns current recording subject Id
        """
        return self._bidsSession.subject

    def setSubId(self) -> None:
        """
        Sets current recording subject Id from value
        in BidsSession
        """
        name = self._bidsSession.subject
        if name is None:
            subid = self._getSubId()
        elif name == "" or name == "sub-":
            subid = ""
        else:
            subid = self.getDynamicField(name,
                                         cleanup=False,
                                         raw=False
                                         )
        if subid is None:
            # Undetermined subject Id, extracting from filename,
            # assuming it bids-formatted
            res = re.search("sub-([a-zA-Z0-9]+)", self.currentFile(False))
            if res:
                subid = res.group(1)
        if subid is None or subid == "":
            logger.error("{}: Unable to determine subject Id from '{}'"
                         .format(self.recIdentity(), name))
            raise ValueError("Invalid subject Id")
        self._bidsSession.unlock_subject()
        self._bidsSession.subject = subid
        self._bidsSession.lock_subject()

    def sesId(self):
        """
        Returns current recording session Id
        """
        return self._bidsSession.session

    def setSesId(self):
        """
        Sets current recording session Id
        """
        name = self._bidsSession.session
        if name is None:
            subid = self._getSesId()
        elif name == "" or name == "ses-":
            subid = ""
        else:
            subid = self.getDynamicField(name,
                                         cleanup=False,
                                         raw=False
                                         )

        if subid is None:
            # Undetermined subject Id, extracting from filename,
            # assuming it bids-formatted
            res = re.search("ses-([a-zA-Z0-9]+)", self.currentFile(False))
            if res:
                subid = res.group(1)
        if subid is None:
            logger.error("{}/{}: Unable to determine session Id from {}"
                         .format(self.recNo(), self.recId(),
                                 name))
            raise ValueError("Invalid session Id")
        self._bidsSession.unlock_session()
        self._bidsSession.session = subid
        self._bidsSession.lock_session()

    def acqTime(self) -> datetime:
        """
        Returns the time corresponding to the first data
        of recording

        Returns
        -------
        datetime
        """
        return self._acqTime

    def setAcqTime(self, t: datetime = None) -> None:
        """
        Sets the recording to given datetime.

        If t is None (default), then datetime determined from
        recording

        Parameters
        ----------
        t: datetime
            datetime to set
        """
        if t is None:
            self._acqTime = self._getAcqTime()
        else:
            self._acqTime = tools.check_type("t", datetime, t)

    def resetAcqTime(self):
        """
        Sets current acqTime to unkown value
        """
        self._acqTime = None

    @property
    def series_no(self):
        return self._series_no

    @series_no.setter
    def series_no(self, val):
        if not isinstance(val, int):
            raise ValueError("{}: series_no must be an int, {} recieved"
                             .format(self.currentFile(), type(val)))
        self._series_no = val

    def recNo(self):
        return self.series_no

    @property
    def series_id(self):
        return self._series_id

    @series_id.setter
    def series_id(self, val):
        if not isinstance(val, str):
            raise ValueError("{}: series_id must be a string, {} recieved"
                             .format(self.currentFile(), type(val)))
        self._series_id = val

    def recId(self):
        return self.series_id

    def recIdentity(self, padding: int = 3, index=True):
        """
        Returns identification string for current recording
        in form {recNo}-{recId}/{index}

        Parameters
        ----------
        prec: int
            how much of padding 0 to add to recNo
        index: bool
            switch to print or not file index

        Returns
        -------
        str
        """
        try:
            if index:
                return "{:0{width}}-{}/{}".format(self.recNo(),
                                                  self.recId(),
                                                  self.index,
                                                  width=padding)
            else:
                return "{:0{width}}-{}".format(self.recNo(),
                                               self.recId(),
                                               width=padding)
        except Exception:
            return self.currentFile()

    def setManufacturer(self, line: str, manufacturers: dict) -> bool:
        """
        Sets manufacturer accordingly to retrieved key line
        Returns true if manufacturer changes

        Parameters
        ----------
        line: str
            key line used to determine manufacturer
        manufacturers: dict
            dictionary with known manufacturer names

        Returns
        -------
        bool:
            True if manufacturer value changes
        """
        manufacturer = "Unknown"
        if line:
            lin = line.lower()
            for man in manufacturers:
                if man in lin:
                    manufacturer = manufacturers[man]
                    break

        if self.manufacturer is None:
            # First time initialisation
            self.manufacturer = manufacturer
            return True

        if manufacturer == self.manufacturer:
            return False
        else:
            self.manufacturer = manufacturer
            return True

    def getCharecteristic(self, field):
        """
        Retrieves given cheracteristic value
        Allowed characteristics without prefix:
            - subject: subject Id
            - session: session Id
            - serieNumber: serie Id
            - serie: serie name
            - index: index of current file in serie
            - nfiles: total number of files in serie
            - filename: name of current file
            - suffix: bids suffix  of current file
            - modality: modality of current file
            - module: name of module
            - placeholder: name to fill manually
            - None: void value
        Allowed characteristics wit prefix:
            - bids:entity : Entity value for current file
            - custom:key : Custom value, stored at key
            - sub_tsv:column : value from participants.tsv
            - rec_tsv:column : Value from scans.tsv
            - fname:query : entity value extracted from filename
            - increment[0-9]*:tag : counts calls of increments of the tag
        """
        prefix = ""
        if ":" in field:
            prefix, query = field.split(":", 1)

        if not prefix:
            if field == "subject":
                return self.subId()
            if field == "session":
                return self.sesId()
            if field == "serieNumber":
                return self.recNo()
            if field == "serie":
                return self.recId()
            if field == "index":
                return self.index + 1
            if field == "nfiles":
                return len(self.files)
            if field == "filename":
                return self.currentFile(False)
            if field == "suffix":
                return self.suffix
            if field == "modality":
                return self._modality
            if field == "module":
                return self._module
            if field == "placeholder":
                logger.warning("{}: Placehoder found"
                               .format(self.recIdentity()))
                return "<<placeholder>>"
            if field == "None":
                return None
            raise CharacteristicError(field)
        else:
            if prefix == "bids":
                return self.labels[query]
            elif prefix == "custom":
                return self.custom[query]
            elif prefix == "sub_tsv":
                return self._bidsSession.sub_values[query]
            # elif prefix == "rec_tsv":
            #     return self._bidsSession.rec_values[query]
            elif prefix == "fname":
                if (search := re.search("(?:^|_){}-([a-zA-Z0-9]+)"
                                        .format(query),
                                        self.currentFile(False))):
                    return search.group(1)
                else:
                    return None
            elif (search := re.fullmatch("increment([0-9]*)", prefix)):
                # The unnamed <<increment>> is calculated in setLabels function
                if not query:
                    raise CharacteristicError("Can't use increment "
                                              "without label")
                result = self._bidsSession.getIncrement(query)
                order = search.group(1)
                if not order:
                    order = '1'
                fstr = "{{:0{}d}}".format(order)
                return fstr.format(result)
            else:
                raise CharacteristicError("Unknown prefix {}".format(prefix))

    ##############################
    # File manipulation methodes #
    ##############################
    def loadFile(self, index: int) -> None:
        """
        Load file at given index. All stored attributes will be recalculated.

        Parameters
        ----------
        index: int
            index of file in registered files list
        """
        path = os.path.join(self._recPath, self.files[index])
        if not self.isValidFile(path):
            raise ValueError("{}: {} is not valid file"
                             .format(self.formatIdentity(), path))

        self.index = index
        self._loadFile(path)
        self.setAcqTime()
        self.attributes = {}
        # for key in self.attributes:
        #     self.attributes[key] = self.getField(key)
        # Updating series No and Id
        self.series_no = self._recNo()
        self.series_id = self._recId()

    def setRecPath(self, folder: str) -> int:
        """
        Set given folder as folder containing all files for serie.
        Returns number of valid recordings in this folder.
        Clears cache and unload current file.

        Parameters
        ----------
        folder: str
            path to folder with recordings, must exist

        Returns
        -------
        int:
            number of found valid recordings

        Raises
        ------
        NotADirectoryError:
            if folder don't exists or not a folder
        """
        if not os.path.isdir(folder):
            raise NotADirectoryError("Path {} is not a folder"
                                     .format(folder))
        self._recPath = os.path.normpath(folder)
        self.clearCache()
        self.files.clear()
        self.index = -1

        for file in sorted(os.listdir(self._recPath)):
            if os.path.basename(file).startswith('.'):
                logger.warning('{}/{}: Ignoring hidden file: {}'
                               .format(self.Module(),
                                       self.Type(),
                                       file))
                continue
            full_path = os.path.join(self._recPath, file)
            if self.isValidFile(full_path):
                self.files.append(file)
        if len(self.files) == 0:
            logger.warning("{}/{}: No valid files found in {}"
                           .format(self.Module(),
                                   self.Type(),
                                   self._recPath
                                   ))
        else:
            self.loadFile(0)
            logger.debug("{}/{}: {} valid files found in {}"
                         .format(self.Module(),
                                 self.Type(),
                                 len(self.files),
                                 self._recPath
                                 ))
        return len(self.files)

    def loadNextFile(self) -> bool:
        """
        Loads next file in serie.
        Returns True in sucess, False othrwise
        """
        if self.index + 1 >= len(self.files):
            return False
        self.loadFile(self.index + 1)
        return True

    def currentFile(self, base: bool = False) -> str:
        """
        Returns the path to currently loaded file

        Parameters
        ----------
        base: bool
            if True, only basename is retrieved, and
            fullpath overwise

        Returns
        -------
        str:
            currently loaded filename
        """
        if self.index >= 0 and self.index < len(self.files):
            if base:
                return self.files[self.index]
            else:
                return os.path.join(self._recPath, self.files[self.index])
        return None

    def recPath(self):
        """
        Returns current recording path
        """
        return self._recPath

    #########################
    # Bids-related methodes #
    #########################
    def bidsify(self, bidsfolder: str) -> None:
        """
        Copy current file to the destination, change the name
        to the bidsified one, and export metadata to json

        Non-existing folders will be created

        Parameters
        ----------
        bidsfolder: str
            path to root of output bids folder

        Returns
        -------
        str:
            path to copied data file
        """
        if not self._bidsSession.isValid():
            raise ValueError("{}: Recording have invalid bids session"
                             .format(self.recIdentity()))
        if not self.isValidModality(self._modality, False):
            logger.warning("{}: Non-BIDS modality {}"
                           .format(self.recIdentity(),
                                   self._modality))

        outdir = os.path.join(bidsfolder,
                              self.getBidsPrefix('/'),
                              self._modality)

        logger.debug("Creating folder {}".format(outdir))
        os.makedirs(outdir, exist_ok=True)

        base, ext = os.path.splitext(self.currentFile(False))
        if ext == ".gz":
            ext = os.path.splitext(base)[1] + ext
        elif self.switches["zipFile"]:
            ext += ".gz"

        bidsname = self.getBidsname()
        # bidsname = os.path.join(outdir, self.getBidsname())

        logger.debug("Copying {} to {}/{}{}".format(self.currentFile(),
                                                    outdir,
                                                    bidsname,
                                                    ext))

        self._copy_bidsified(outdir, bidsname, ext)
        self._post_copy_bidsified(outdir, bidsname, ext)

        with open(os.path.join(outdir, bidsname + ".json"), "w") as f:
            js_dict = self.exportMeta()
            js_dict = {key: val
                       for key, val in js_dict.items()
                       if val is not None}
            json.dump(js_dict, f, indent=2, cls=ExtendEncoder)

        self.rec_BIDSvalues["filename"] = os.path.join(self.Modality(),
                                                       bidsname
                                                       + ext)
        if self.acqTime() is None:
            self.rec_BIDSvalues["acq_time"] = None
        else:
            self.rec_BIDSvalues["acq_time"] = self.acqTime().replace(
                    microsecond=0,
                    tzinfo=None)

        scans = os.path.join(bidsfolder,
                             self.getBidsPrefix('/'),
                             '{}_scans'.format(self.getBidsPrefix()))
        scans_tsv = scans + ".tsv"
        scans_json = scans + ".json"

        if os.path.isfile(scans_tsv):
            with open(scans_tsv, "a") as f:
                f.write(self.rec_BIDSfields.GetLine(
                    self.rec_BIDSvalues))
                f.write('\n')
        else:
            with open(scans_tsv, "w") as f:
                f.write(self.rec_BIDSfields.GetHeader())
                f.write('\n')
                f.write(self.rec_BIDSfields.GetLine(
                    self.rec_BIDSvalues))
                f.write('\n')
            self.rec_BIDSfields.DumpDefinitions(scans_json)
        return os.path.join(outdir, bidsname + ext)

    def setLabels(self, run):
        """
        Set the BIDS tags (labels) according to given run

        Parameters
        ----------
        run: bidsmap.Run
            Matching Run containing bids tags
        """

        self.suffix = ""
        self._modality = unknownmodality
        self.labels = OrderedDict()
        if not run:
            return

        self._modality = run.modality

        # ignored modality
        if run.modality == ignoremodality:
            return

        incr_key = None
        tag = ""
        self.labels = OrderedDict.fromkeys(run.entity)
        self.suffix = self.getDynamicField(run.suffix)
        for key in run.entity:
            if isinstance(run.entity[key], str) \
                    and re.fullmatch("<<increment[0-9]*>>", run.entity[key]):
                val = "1"
                incr_key = key
                tag = run.entity[key][2:-2]
            else:
                val = self.getDynamicField(run.entity[key])
            self.labels[key] = val
        if incr_key:
            bids_name = self.getBidsname()
            tag = "<<{}:{}>>".format(tag, bids_name)
            val = self.getDynamicField(tag)
            self.labels[incr_key] = val

        for key, val in run.json.items():
            self.metaAuxiliary[key] = deepcopy(val)

    def getBidsPrefix(self, sep: str = '_') -> str:
        """
        Generates the subject/session prefix using separator,
        like sub-123_ses-456

        Parameters
        ----------
        sep: str
            separator used for subject and session fields

        Returns
        -------
        str
        """
        subid = self.subId()
        sesid = self.sesId()
        if not subid:
            logger.error("{}: Subject Id not defined"
                         .format(self.recIdentity()))
            raise ValueError("Subject Id not defined")
        if sesid:
            subid += sep + sesid
        return subid

    def getBidsname(self):
        """
        Generates bidsified name based on saved tags and suffixes

        Returns
        -------
        str:
            bidsified name
        """
        tags_list = [self.getBidsPrefix()]
        for key, val in self.labels.items():
            if val:
                tags_list.append(tools.cleanup_value(val, key + "-"))

        if self.suffix:
            tags_list.append(tools.cleanup_value(self.suffix))
        return "_".join(tags_list)

    #############################################
    # JSON sidecar meta-fields related methodes #
    #############################################
    def setupMetaFields(self, definitions: dict) -> None:
        """
        Setup json fields to values from given dictionary.

        Dictionary must contain key "Unknown", and keys
        correspondand to each of manufacturer.

        Corresponding values are dictionaries with json
        metafields names (as defined in MRI metafields)
        as keys and a tuple of DynamicField name, default value
        If default value is None, no default is defined.

        Parameters
        ----------
        definitions: dict
            dictionary with metadata fields definitions
        """

        self.meta_shorcut = definitions.get("Unknown", {})
        self.meta_shorcut.update(definitions.get(self.manufacturer, {}))

    def expandSidecar(self, model,
                      sidecar: OrderedDict = None,
                      use_placeholder: bool = False):
        """
        Expand provided sidecar (OrderedDict) with metafields
        retrieved from loaded schema based on model.

        If sidecar is None, the metaAuxiliary is used.
        If use_placeholder, fields that are in schema but not
        retrieved will be expanded with corresponding placeholder.
        Additionally, if use_placeholder, the required and
        retrieved variables will be expanded explicetly.

        The fields will be attempted to be retrieved in following
        order:
            custom variables
            shorctuts defined for given data format
            metadata from file header

        Parameters:
        -----------
            model: str
                Model name with which expand sidecar
            sidecar: OrderedDict, optional
                sidecar to expand, if None, the self.metaAuxiliary
                will be used
            use_placeholder: bool, optional
                If False (default) all not retrieved fields will
                be ignored.
                If True, all not retrieved fields will be replaced
                by corresponding placeholder.
        """
        if sidecar is None:
            sidecar = self.metaAuxiliary

        for key, placeholder in model.items():
            # Already defined
            if key in sidecar:
                continue
            test_key = ""
            if key in self.custom:
                test_key = "<<custom:{}>>".format(key)
            elif key in self.meta_shorcut:
                test_key = self.meta_shorcut[key]
            else:
                test_key = "<{}>".format(key)
            res = self.getDynamicField(test_key, warning=False,
                                       cleanup=False, raw=True)
            if res is None:
                # Test key field not found
                if use_placeholder:
                    sidecar[key] = placeholder
            else:
                if not use_placeholder or placeholder:
                    sidecar[key] = test_key

    def exportMeta(self, keys: list = []) -> dict:
        """
        Retrieves metadata values for sidecar json

        Returns
        -------
        dict:
            resulting dictionary
        """
        if not keys:
            keys = self.metaAuxiliary.keys()

        exp = {}
        for key in keys:
            val = self.metaAuxiliary.get(key, None)
            if val is None:
                continue

            if isinstance(val, list):
                res = [self.getDynamicField(v, warning=False,
                                            raw=True, cleanup=False)
                       for v in val]
            elif isinstance(val, str):
                res = self.getDynamicField(val, warning=False,
                                           raw=True, cleanup=False)
            else:
                res = val
            if res is not None:
                exp[key] = res
        return exp

    #####################################
    # Recording identification methodes #
    #####################################
    def matchAttribute(self, attribute: str, pattern: str) -> bool:
        """
        Return True if given attribute value matches pattern,
        False overwise

        Parameter
        ---------
        attribute: str
            Attribute name to match
        pattern: str
            Pattern to match

        Returns
        -------
        bool
        """
        if attribute.startswith('<'):
            attval = self.getDynamicField(attribute,
                                          cleanup=False,
                                          raw=True)
        else:
            attval = self.getAttribute(attribute)
        if attval is None:
            return False
        if pattern is None:
            return True
        if isinstance(pattern, list):
            for val in pattern:
                if tools.match_value(attval, val):
                    return True
            return False
        return tools.match_value(attval, pattern)

    def match_run(self, run):
        """
        Returns True if recording matches given run, False
        overwise.

        Parameters
        ----------
        run: bidsmap.Run
            run to match
        Returns
        -------
        bool
        """
        if run is None:
            logger.debug("{}/{}: trying to match empty runs"
                         .format(self.Module(),
                                 self.Type()))
            return False
        match_one = False
        match_all = True
        if not run.attribute:
            match_one = True
        for attrkey, attrvalue in run.attribute.items():
            if attrvalue is None:
                continue
            res = self.matchAttribute(attrkey, attrvalue)
            match_one = match_one or res
            match_all = match_all and res
            if not match_all:
                break
        return match_one and match_all


class ExtendEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime("%Y-%m-%dT%H:%M:%S.%f")
        if isinstance(obj, time):
            return obj.strftime("%H:%M:%S.%f")
        if isinstance(obj, date):
            return obj.strftime("%Y-%m-%d")
        if isinstance(obj, bytes):
            try:
                return obj.decode("ascii")
            except UnicodeDecodeError:
                return "<bytes>"
        if isinstance(obj, numpy.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)
