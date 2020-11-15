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

from datetime import datetime, date, time
from collections import OrderedDict

from .abstract import abstract
from tools import tools
from bidsMeta import MetaField
from bidsMeta import BIDSfieldLibrary

from bidsmap import Run

from bids import BidsSession

from ._constants import ignoremodality, unknownmodality
from .common import action_value

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
                 # json meta variables
                 "metaAuxiliary",
                 "metaFields_req",
                 "metaFields_rec",
                 "metaFields_opt",
                 # tsv meta variables
                 "rec_BIDSvalues",
                 "sub_BIDSvalues",
                 # general attributes
                 "_acqTime",
                 "manufacturer",
                 "isBidsValid",
                 "encoding",
                 "zip"
                 ]

    _module = "base"
    _type = "None"

    bidsmodalities = dict()

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
        self.attributes = dict()
        self.custom = dict()
        self.labels = OrderedDict()
        self.suffix = ""
        self._modality = unknownmodality
        self._bidsSession = None

        self.metaFields_req = dict()
        self.metaFields_rec = dict()
        self.metaFields_opt = dict()
        self.metaAuxiliary = dict()
        self.rec_BIDSvalues = self.rec_BIDSfields.GetTemplate()
        self.sub_BIDSvalues = self.sub_BIDSfields.GetTemplate()

        self._acqTime = None
        self.manufacturer = None
        self.isBidsValid = True
        self.encoding = "ascii"

        self.zip = False

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
        if self.zip:
            with open(self.currentFile(), 'rb') as f_in:
                with gzip.open(out_fname + ".gz", 'wb') as f_out:
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
        shutil.copy2(self.currentFile(), destination)

        # creating header dump for BIDS invalid formats
        if not self.isBidsValid:
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
        return os.path.join(destination, self.currentFile(True))

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
        if not os.path.exists(file):
            raise FileNotFoundError("File {} not found or not a file"
                                    .format(file))
        if not os.access(file, os.R_OK):
            raise PermissionError("File {} not readable"
                                  .format(file))
        try:
            return cls._isValidFile(file)
        except Exception:
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
        if modality in cls.bidsmodalities:
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
            return default
        for prefix in reversed(actions):
            if isinstance(result, list):
                for i, val in enumerate(result):
                    result[i] = self._transformField(val, prefix)
            elif isinstance(result, dict):
                for i, val in result.items():
                    result[i] = self._transformField(val, prefix)
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

    def getDynamicField(self, field: str,
                        default: object = None,
                        cleanup: bool = True, raw: bool = False):
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
        """
        if not isinstance(field, str) or field == "":
            return field
        res = ""
        start = 0
        while start < len(field):
            pos = field.find('<', start)
            if pos < 0:
                res += field[start:]
                break
            res += field[start:pos]

            try:
                if field[pos + 1] == "<":
                    pos += 2
                    seek = ">>"
                else:
                    pos += 1
                    seek = ">"
                pos2 = field.find(seek, pos)
                if pos2 < 0:
                    raise IndexError("closing {} from {} not found in {}"
                                     .format(seek, pos, field))
                query = field[pos:pos2]
                if seek == '>':
                    result = self.getAttribute(query, default)
                    if result is None:
                        logger.warning("{}: Can't find '{}' "
                                       "attribute from '{}'"
                                       .format(self.recIdentity(),
                                               query, field))
                        if not raw:
                            result = query
                        else:
                            result = None
                else:
                    prefix = ""
                    if ":" in query:
                        prefix, query = query.split(":", 1)
                    if prefix == "":
                        result = self._getCharacteristic(query)
                    elif prefix == "bids":
                        result = self.labels[query]
                    elif prefix == "custom":
                        result = self.custom[query]
                    elif prefix == "sub_tsv":
                        # result = self.sub_BIDSvalues[query]
                        result = self._bidsSession.sub_values[query]
                    elif prefix == "rec_tsv":
                        result = self._bidsSession.rec_values[query]
                    elif prefix == "fname":
                        search = re.search("{}-([a-zA-Z0-9]+)".format(query),
                                           self.currentFile(False))
                        if search:
                            result = search.group(1)
                        else:
                            logger.warning("{}: Can't find '{}' "
                                           "attribute from '{}'"
                                           .format(self.recIdentity(),
                                                   query,
                                                   self.currentFile(False)))
                            if not raw:
                                result = query
                            else:
                                result = None
                    else:
                        raise KeyError("Unknown prefix {}".format(prefix))
                # if field is composed only of one entry
                if raw and pos2 - pos + 2 * len(seek) == len(field):
                    return result
                res += str(result)
                start = pos2 + len(seek)
            except Exception as e:
                logger.error("{}: Malformed field "
                             "'{}': {}"
                             .format(self.recIdentity(), field, str(e)))
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
                         .format(self.recIdentity, name))
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

    def _getCharacteristic(self, field):
        """
        Retrieves given cheracteristic value
        Allowed characteristics:
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
        """
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
            return self.Module
        if field == "placeholder":
            logger.warning("{}: Placehoder found"
                           .format(self.recIdentity()))
            return "<<placeholder>>"
        if field == "None":
            return None

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

        self._loadFile(path)
        self.setAcqTime()
        self.index = index
        self.attributes = {}
        # for key in self.attributes:
        #     self.attributes[key] = self.getField(key)

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
            logger.error("{}: Invalid modality {}"
                         .format(self.recIdentity(),
                                 self._modality))
            raise ValueError("Invalid modality")

        outdir = os.path.join(bidsfolder,
                              self.getBidsPrefix('/'),
                              self._modality)

        logger.debug("Creating folder {}".format(outdir))
        os.makedirs(outdir, exist_ok=True)

        ext = os.path.splitext(self.currentFile(False))[1]
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

    def setLabels(self, run: Run = None):
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

        if run.modality in self.bidsmodalities:
            self._modality = run.modality
            tags = set(run.entity)\
                - set(self.bidsmodalities[run.modality])
            if tags:
                if not run.checked:
                    logger.warning("{}: Naming schema not BIDS"
                                   .format(self.recIdentity()))
                self.labels = OrderedDict.fromkeys(run.entity)
            else:
                self.labels = OrderedDict.fromkeys(
                        self.bidsmodalities[run.modality])
            self.suffix = self.getDynamicField(run.suffix)
            for key in run.entity:
                val = self.getDynamicField(run.entity[key])
                self.labels[key] = val
        elif run.modality == ignoremodality:
            self._modality = run.modality
            return
        else:
            logger.error("{}/{}: Unregistered modality {}"
                         .format(self.get_rec_id(),
                                 self.index,
                                 run.modality))

        self.metaAuxiliary = dict()
        for key, val in run.json.items():
            if key:
                if isinstance(val, list):
                    self.metaAuxiliary[key] = [
                            MetaField(key, None,
                                      self.getDynamicField(v,
                                                           cleanup=False,
                                                           raw=True))
                            for v in val]
                else:
                    self.metaAuxiliary[key] = MetaField(
                            key, None,
                            self.getDynamicField(val,
                                                 cleanup=False,
                                                 raw=True))

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
    def reserMetaFields(self) -> None:
        """
        Virtual function
        Resets currently defined meta fields dictionaries
        to None values
        """
        raise NotImplementedError

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
        if self.manufacturer in definitions:
            meta = definitions[self.manufacturer]
        else:
            meta = None
        meta_default = definitions["Unknown"]

        for metaFields in (self.metaFields_req,
                           self.metaFields_rec,
                           self.metaFields_opt):
            for mod in metaFields:
                for key in metaFields[mod]:
                    if meta and key in meta:
                        val = meta[key]
                        if isinstance(val, list):
                            metaFields[mod][key] = [MetaField(f[0],
                                                              scaling=None,
                                                              default=f[1])
                                                    for f in val]
                        else:
                            metaFields[mod][key]\
                                = MetaField(val[0],
                                            scaling=None,
                                            default=val[1])
                            continue
                    if key in meta_default:
                        val = meta_default[key]
                        if isinstance(val, list):
                            metaFields[mod][key] = [MetaField(f[0],
                                                              scaling=None,
                                                              default=f[1])
                                                    for f in val]
                        else:
                            metaFields[mod][key]\
                                = MetaField(val[0],
                                            scaling=None,
                                            default=val[1])

    def testMetaFields(self):
        """
        Test all metafields values and resets not found ones
        """
        for metaFields in (self.metaFields_req,
                           self.metaFields_rec,
                           self.metaFields_opt):
            for mod in metaFields:
                for key, field in metaFields[mod].items():
                    if isinstance(field, list):
                        continue
                    if field is None or "<<" in field.name:
                        continue
                    res = None
                    try:
                        res = self.getDynamicField(field.name,
                                                   default=field.default,
                                                   raw=True,
                                                   cleanup=False)
                    except Exception:
                        metaFields[mod][key] = None
                        pass
                    if res is None:
                        metaFields[mod][key] = None

    def generateMeta(self) -> dict:
        """
        Fills standard meta values. Must be called before exporting
        these meta-data into json
        """
        if not self._modality:
            logger.error("{}/{}: Modality not defined"
                         .format(self.Module(), self.Type()))
            raise ValueError("Modality wasn't defined")

        mod = self._modality
        if mod in self.metaFields_req:
            for key, field in self.metaFields_req[mod].items():
                if field is None:
                    continue
                if key not in self.metaAuxiliary:
                    field.value = self.__getMetaFieldSecure(field,
                                                            field.default)
        if mod in self.metaFields_rec:
            for key, field in self.metaFields_rec[mod].items():
                if field is not None and key not in self.metaAuxiliary:
                    field.value = self.__getMetaFieldSecure(field,
                                                            field.default)
        if mod in self.metaFields_opt:
            for key, field in self.metaFields_opt[mod].items():
                if field is not None and key not in self.metaAuxiliary:
                    field.value = self.__getMetaFieldSecure(field,
                                                            field.default)
        mod = "__common__"
        if mod in self.metaFields_req:
            for key, field in self.metaFields_req[mod].items():
                if field is not None and key not in self.metaAuxiliary:
                    field.value = self.__getMetaFieldSecure(field,
                                                            field.default)
        if mod in self.metaFields_rec:
            for key, field in self.metaFields_rec[mod].items():
                if field is not None and key not in self.metaAuxiliary:
                    field.value = self.__getMetaFieldSecure(field,
                                                            field.default)
        if mod in self.metaFields_opt:
            for key, field in self.metaFields_opt[mod].items():
                if field is not None and key not in self.metaAuxiliary:
                    field.value = self.__getMetaFieldSecure(field,
                                                            field.default)

    def exportMeta(self) -> dict:
        """
        Exports recording metadata into dictionary structure

        The metadata keys are put in order:
            1. The auxiliary (defined in bidsmap)
            2. Modality required
            3. Modality recommended
            4. Modality optional
            5. Common required
            6. Common recommended
            7. Common optional

        Already existing keys are ignored

        Returns
        -------
        dict:
            resulting dictionary
        """
        exp = dict()
        self.__fillMetaDict(exp, self.metaAuxiliary,
                            required=False,
                            ignore_null=True)
        mod = self._modality
        if mod in self.metaFields_req:
            self.__fillMetaDict(exp, self.metaFields_req[mod],
                                required=True,
                                ignore_null=False)
        if mod in self.metaFields_rec:
            self.__fillMetaDict(exp, self.metaFields_rec[mod],
                                required=False,
                                ignore_null=False)
        if mod in self.metaFields_opt:
            self.__fillMetaDict(exp, self.metaFields_opt[mod],
                                required=False,
                                ignore_null=False)
        mod = "__common__"
        if mod in self.metaFields_req:
            self.__fillMetaDict(exp, self.metaFields_req[mod],
                                required=True,
                                ignore_null=False)
        if mod in self.metaFields_rec:
            self.__fillMetaDict(exp, self.metaFields_rec[mod],
                                required=False,
                                ignore_null=False)
        if mod in self.metaFields_opt:
            self.__fillMetaDict(exp, self.metaFields_opt[mod],
                                required=False,
                                ignore_null=False)
        return exp

    def __fillMetaDict(self,
                       exportDict: dict, metaFields: dict,
                       required: bool, ignore_null: bool) -> None:
        """
        Helper function to fill exportDict by values from metaFields dict
        If key is already filled, it is not updated.

        If required is true, missing values will produce a warning

        Parameters
        ----------
        exportDict: dict
            dictionary to fill
        metaFields: dict
            dictionary with betaField as values
        required: bool
            switch if given values are required or not
        ignore_null: bool
            switch if empty values must be filled
        """
        for key, field in metaFields.items():
            if key in exportDict:
                continue
            if not field:
                if required:
                    logger.warning("{}: Required field {} not set"
                                   .format(self.recIdentity(),
                                           key))
                if not ignore_null:
                    exportDict[key] = None
                continue

            if isinstance(field, list):
                exportDict[key] = [f.value for f in field]
            else:
                exportDict[key] = field.value

    def fillMissingJSON(self, run: Run) -> None:
        """
        Completes missing values from JSON dictionary in given Run

        Required parameters are filled with '<<placeholder>>';
        Recommended parameters are filled with '';
        Optional parameters are filled with None

        Also checks if existing JSON fields are interpretable

        Parameters
        ----------
        run: Run
            Run object with json dictionary to fill
        """
        modality = self.Modality()
        if modality == ignoremodality or modality == unknownmodality:
            return

        if modality in self.metaFields_req:
            for key, field in self.metaFields_req[modality].items():
                if key in run.json:
                    continue
                if self.__getMetaFieldSecure(field, None) is None:
                    run.json[key] = "<<placeholder>>"
        if modality in self.metaFields_rec:
            for key, field in self.metaFields_rec[modality].items():
                if key in run.json:
                    continue
                if self.__getMetaFieldSecure(field, None) is None:
                    run.json[key] = ""
        if modality in self.metaFields_opt:
            for key, field in self.metaFields_opt[modality].items():
                if key in run.json:
                    continue
                if self.__getMetaFieldSecure(field, None) is None:
                    run.json[key] = None
        if "__common__" in self.metaFields_req:
            for key, field\
                    in self.metaFields_req["__common__"].items():
                if key in run.json:
                    continue
                if self.__getMetaFieldSecure(field, None) is None:
                    run.json[key] = "<<placeholder>>"
        if "__common__" in self.metaFields_rec:
            for key, field\
                    in self.metaFields_rec["__common__"].items():
                if key in run.json:
                    continue
                if self.__getMetaFieldSecure(field, None) is None:
                    run.json[key] = ""
        if "__common__" in self.metaFields_opt:
            for key, field\
                    in self.metaFields_opt["__common__"].items():
                if key in run.json:
                    continue
                if self.__getMetaFieldSecure(field, None) is None:
                    run.json[key] = None

    def __getMetaFieldSecure(self, field: MetaField, fallback):
        if field is None:
            return fallback
        try:
            val = self.getDynamicField(field.name,
                                       default=fallback,
                                       raw=True, cleanup=False)
        except Exception:
            return fallback
        if val is None:
            return fallback
        return val

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
                return obj.decode(self.encoding)
            except UnicodeDecodeError:
                return "<bytes>"
        if isinstance(obj, numpy.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)
