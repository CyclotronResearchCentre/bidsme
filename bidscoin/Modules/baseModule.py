import os
import shutil
import logging
import json
import re
from datetime import datetime
from collections import OrderedDict

from tools import tools
from bidsMeta import MetaField
from bidsMeta import BIDSfieldLibrary

from ..bidsmap import Run

logger = logging.getLogger(__name__)


class baseModule(object):
    """
    Base class from which all modules should inherit
    """
    __slots__ = [
                 # bids name values
                 "_modality",
                 "Subject",
                 "Session",
                 "labels",
                 "suffix",
                 # recording attributes
                 "attributes",
                 "main_attributes",
                 # local file variables
                 "_index", 
                 "files",
                 "_recPath",
                 # json meta variables
                 "metaAuxiliary",
                 "metaFields",
                 # tsv meta variables
                 "rec_BIDSvalues",
                 "sub_BIDSvalues"
                 ]

    _Module = "base"
    _Type = "None"

    bidsmodalities = dict()
    ignoremodality = '__ignore__'
    unknownmodality = '__unknown__'

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

    def __init__(self, rec_path=""):
        self.files = list()
        self._recPath = ""
        self.index = -1
        self.attributes = dict()
        self.labels = OrderedDict()
        self.suffix = ""
        self.modality = self.unknownmodality
        self.Subject = None
        self.Session = None
        self.main_attributes = set()

        self.metaFields = dict()
        self.metaAuxiliary = dict()
        self.rec_BIDSvalues = dict()
        self.sub_BIDSvalues = dict()

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
        if not os.path.isfile(file):
            raise FileNotFoundError("File {} not found or not a file"
                                    .format(file))
        if not os.access(file, os.R_OK):
            raise PermissionError("File {} not readable"
                                  .format(file))
        return cls._isValidFile(file)

    @classmethod
    def _isValidFile(cls, file:str) -> bool:
        """
        Virtual function that checks if file is valid one
        """
        raise NotImplementedError

    @classmethod
    def getModule(cls):
        """
        returns Module name of current class
        """
        return cls._Module

    @classmethod
    def getType(cls):
        """
        returns file type of current class
        """
        return cls._Type

    def clearCache(self) -> None:
        """
        Virtual function that clears cache of current file
        """
        pass

    def loadFile(self, index: int) -> None:
        """
        Virtual function that load file at index of current serie
        """
        raise NotImplementedError

    def acqTime(self) -> datetime:
        """
        Virtual function that returns acquisition time, i.e.
        time corresponding to the first data of file
        """
        raise NotImplementedError

    def dump(self):
        """
        Virtual function that returns list of all meta-data
        associated with current file
        """
        return NotImplementedError

    def getField(self, field: str, default=None, prefix=':',separator='/'):

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

        field = field.split(prefix, 1)
        if len(field) == 2:
            prefix, field = field
        else:
            prefix = ""
            field = field[0]
        result = self._getField(field.split(separator), prefix)

        if result is None:
            return default
        return result

    def _getField(self, field: list, prefix: str=""):
        """
        Virtual function that retrives the field value 
        from recording metadata.

        Parameters
        ----------
        field: list(str)
            list of nested values (or just one element) 
            giving position of field to retrieve
        prefix: str
            prefix indicating the transformation function 
            to call on retrieved value

        Returns
        -------
            retrieved value or None if field not found

        Raises
        ------
        TypeError:
            if field value is not applicable to prefix 
            function
        KeyError:
            if prefix function is not defined
        """
        raise NotImplementedError

    def bidsify(self, bidsfolder: str) -> None:
        """
        Copy current file to the destination, change the name
        to the bidsified one, and export metadata to json

        Non-existing folders will be created

        Parameters
        ----------
        bidsfolder: str
            path to root of output bids folder
        """
        if self.Subject is None\
                or self.Session is None\
                or self.Modality is None:
            raise ValueError("Recording missing defined subject, "
                             "session and/or modality")
        outdir = os.path.join(bidsfolder, 
                              self.Subject,
                              self.Session,
                              self.Modality)
        ext = os.path.splitext(self.currentFile(False))[1]
        basename = "{}/{}".format(bidsfolder,self.get_bidsname())

        logger.debug("Creating folder {}".format(outdir))
        os.makedirs(outdir, exist_ok=True)
        logger.debug("Copying {} to {}".fomat(self.currentFile(),
                                              basename + ext))
        shutil.copy2(self.currentFile(),
                     basename + ext)
        with open(basename + ".json", "w") as f:
            js_dict = self.exportMeta()
            json.dump(js_dict, f, indent=2)

        self._post_copy(basename, ext)

    def _post_copy(self, basename: str, ext: str) -> None:
        """
        Virtual function used to internally adapt bidsified 
        files to new name.
        The data file is retrieved by basename + ext.
        Accompanying json file is retrieved by basename + ".json"

        Parameters
        ----------
        basename: str
            full path to file without extension
        ext: str
            extension to data file
        """
        pass

    def copy_raw(self, destination: str) -> None:
        """
        Virtual function to Copy raw (non-bidsified) file
        to destination. 
        Destination is intended to be directory that should 
        be created if needed.

        Parameters
        ----------
        destination: str
            output folder to copied files
        """
        os.makedirs(destination, exist_ok=True)
        shutil.copy2(self.currentFile(), destination)

    def getAttribute(self, attribute: str,
                     default: None):
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
        if attribute in self._attributes:
            return self._attributes[attribute]
        else:
            res = self.getField(attribute, default)
            self._attributes[attribute] = res
            return res

    def getDynamicField(self, field: str,
                        cleanup: bool=True, raw: bool=False):
        if not field or not isinstance(field, str):
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
                    result = self.getAttribute(query)
                else:
                    prefix = ""
                    if ":" in query:
                        prefix, query = query.split(":",1)
                    if prefix == "":
                        result = self.getCharacteristic(query)
                    elif prefix == "bids":
                        result = self.labels[query]
                    elif prefix == "sub_tsv":
                        result = self.sub_BIDSvalues[query]
                    elif prefix == "rec_tsv":
                        result = self.sub_BIDSvalues[query]
                    else:
                        raise KeyError("Unknown prefix {}".format(prefix))
                if result is None:
                    raise KeyError("Cant interpret {} at {} from {}"
                                   .format(query, pos, field))
                # if field is composed only of one entry
                if raw and pos2 - pos + 2 * len(seek) == len(field):
                    return result
                res += str(result)
                start = pos2 + len(seek)
            except Exception as e:
                logger.error("Malformed field '{}': {}".format(field, str(e)))
                raise
        if cleanup:
            res = tools.cleanup_value(res)
        return res

    def getRecNo(self):
        """
        Virtual function returning current serie number 
        (i.e. numero of scan in session).
        getRecNo together with getRecId must uniquely 
        identify serie within session
        """
        raise NotImplementedError

    def getRecId(self):
        """
        Virtual function returning current serie id
        (i.e. name of scan in session).
        getRecNo together with getRecId must uniquely 
        identify serie within session
        """
        raise NotImplementedError

    def loadNextFile(self) -> bool:
        """
        Loads next file in serie. 
        Returns True in sucess, False othrwise
        """
        if self._index + 1 >= len(self.files):
            return False
        self.loadFile(self._index + 1)
        return True

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

    def isCompleteRecording(self) -> bool:
        """
        Virtual function.
        Returns True if current recording is complete,
        False overwise.
        """
        raise NotImplementedError

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
    def getValidFile(self, folder: str, index: int=0) -> int:
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
                       .format(self.getModule(), self.getType(), 
                               index, folder))
        return None

    def getCurrentFile(self, base: bool=False) -> str:
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
        if self._index >= 0 and self._index < len(self.files):
            if base:
                return self.files[self._index]
            else:
                return os.path.join(self._recPath, self.files[self._index])
        return None

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
        self._files.clear()
        self._index = -1

        for file in sorted(os.listdir(self._recPath)):
            if os.path.basename(file).startswith('.'):
                logger.warning('{}/{}: Ignoring hidden file: {}'
                               .format(self.getModule(),
                                       self.getType(),
                                       file))
                continue
            full_path = os.path.join(self._recPath, file)
            if self.isValidFile(full_path):
                self._files.append(file)
        if len(self._files) == 0:
            logger.warning("{}/{}: No valid files found in {}"
                           .format(self.getModule(),
                                   self.getType(),
                                   self._recPath
                                   ))
        else:
            self.loadFile(0)
            logger.debug("{}/{}: {} valid files found in {}"
                         .format(self.getModule(),
                                 self.getType(),
                                 len(self._files),
                                 self._recPath
                                 ))
        return len(self._files)

    def setLabels(self, run: Run=None):
        """
        Set the BIDS tags (labels) according to given run

        Parameters
        ----------
        run: bidsmap.Run
            Matching Run containing bids tags
        """

        self._suffix = ""
        self._modality = self.unknownmodality
        self._labels = OrderedDict()
        if not run:
            return

        if run.modality in self.bidsmodalities:
            self._modality = run.modality
            tags = set(self.bidsmodalities[run.modality]) \
                - set(run.entity)
            if tags:
                if not run.checked:
                    logger.warning("{}-{}/{}: Naming schema not BIDS"
                                   .format(self.get_rec_no(),
                                           self.get_rec_id(),
                                           self.index))
                self.labels = OrderedDict.fromkeys(run.entity)
            else:
                self.labels = OrderedDict.fromkeys(
                        self.bidsmodalities[run.modality])
            self.suffix = self.getDynamicField(run.suffix)
            for key in run.entity:
                val = self.getDynamicField(run.entity[key])
                self.labels[key] = val
        elif run.modality == self.ignoremodality:
            self._modality = run.modality
            return
        else:
            logger.error("{}/{}: Unregistered modality {}"
                         .format(self.get_rec_id(),
                                 self.index,
                                 run.modality))

        self.metaAuxiliary = dict()
        for key, val in run.json.items():
            if key and run.json[key]:
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

    def match_attribute(self, attribute: str, pattern:str) -> bool:
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
        if not pattern:
            return True
        attval = self.getAttribute(attribute)
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
                         .format(self.getModule(),
                                 self.getType()))
            return False
        match_one = False
        match_all = True
        for attrkey, attrvalue in run._attribute.items():
            if not attrvalue:
                continue
            res = self.matchAttribute(attrkey, attrvalue)
            match_one = match_one or res
            match_all = match_all and res
            if not match_all:
                break
        return match_one and match_all

    def getSubId(self):
        """
        Returns the current recording subject Id. First it tries 
        to get it from saved value, if none, get from current 
        file path

        Returns
        -------
        str:
            sub-<Id>
        """
        if not self.Subject:
            subid = self.getIdFolder("sub-")
        else: 
            subid = self.getDynamicField(self.Subject,
                                         cleanup=False,
                                         default="")
        if subid == "":
            return subid
        return 'sub-' + tools.cleanup_value(re.sub('^sub-', '', subid))

    def getSesId(self):
        """
        Returns the current recording session Id. First it tries 
        to get it from saved value, if none, get from current 
        file path

        Returns
        -------
        str:
            ses-<Id>
        """
        if not self.Session:
            subid = self.getIdFolder("ses-")
        else: 
            subid = self.getDynamicField(self.Session,
                                         cleanup=False, 
                                         default="")
        if subid == "":
            return subid
        return 'ses-' + tools.cleanup_value(re.sub('^ses-', '', subid))

    def get_bidsname(self):
        """
        Generates bidsified name based on saved tags and suffixes

        Returns
        -------
        str:
            bidsified name
        """
        tags_list = list()
        subid = self.getSubId()
        if subid:
            tags_list.append(subid)
        sesid = self.getSesId()
        if sesid:
            tags_list.append(sesid)
        for key, val in self._labels.items():
            if val:
                tags_list.append(key + "-"
                                 + tools.cleanup_value(val))

        if self.suffix:
            tags_list.append(tools.cleanup_value(self.suffix))
        return "_".join(tags_list)

    def getIdFolder(self, prefix: str):
        if self._recPath == "":
            logger.error("Recording path not defined")
            return

        # recording path means to be organized as
        # ..../sub-xxx/[ses-yyy]/sequence/files
        try:
            subid = self._recPath.rsplit("/" + prefix, 1)[1]\
                    .split(os.sep)[0]
        except Exception:
            raise ValueError("Failed to extract '{}' form {}"
                             .format(prefix, self._recPath))
        return subid


    @classmethod
    def isValidModality(cls, modality: str,
                        include_unknown: bool = True) -> bool:
        passed = False
        if include_unknown and modality == cls.ignoremodality:
            passed = True
        if modality in cls.bidsmodalities:
            passed = True
        return passed
