import os
import shutil
import logging
import json
from datetime import datetime
from collections import OrderedDict

from tools import tools
from bidsMeta import MetaField
from bidsMeta import BIDSfieldLibrary

from bidsmap import Run

from bids import BidsSession

from ._constants import ignoremodality, unknownmodality

logger = logging.getLogger(__name__)


class baseModule(object):
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
                 # local file variables
                 "index",
                 "files",
                 "_recPath",
                 # json meta variables
                 "metaAuxiliary",
                 "metaFields",
                 # tsv meta variables
                 "rec_BIDSvalues",
                 "sub_BIDSvalues"
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
        self.labels = OrderedDict()
        self.suffix = ""
        self._modality = unknownmodality
        self._bidsSession = None

        self.metaFields = dict()
        self.metaAuxiliary = dict()
        self.rec_BIDSvalues = self.rec_BIDSfields.GetTemplate()
        self.sub_BIDSvalues = self.sub_BIDSfields.GetTemplate()

    #########################
    # Pure virtual methodes #
    #########################
    @classmethod
    def _isValidFile(cls, file: str) -> bool:
        """
        Virtual function that checks if file is valid one
        """
        raise NotImplementedError

    def _loadFile(self, path: str) -> None:
        """
        Virtual function that load file at given path

        Parameters
        ----------
        path: str
            path to file to load
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

    def _getField(self, field: list, prefix: str = ""):
        """
        Virtual function that retrives the field value
        from recording metadata. field is garanteed to be
        non-empty

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

    def recNo(self):
        """
        Virtual function returning current serie number
        (i.e. numero of scan in session).
        recNo together with recId must uniquely
        identify serie within session
        """
        raise NotImplementedError

    def recId(self):
        """
        Virtual function returning current serie id
        (i.e. name of scan in session).
        recNo together with recId must uniquely
        identify serie within session
        """
        raise NotImplementedError

    def isCompleteRecording(self) -> bool:
        """
        Virtual function.
        Returns True if current recording is complete,
        False overwise.
        """
        raise NotImplementedError

    def _getSubId(self) -> str:
        """
        Virtual function
        Returns subject id as defined in metadata
        """
        raise NotImplementedError

    def _getSesId(self) -> str:
        """
        Virtual function
        Returns session id as defined in metadata
        """
        raise NotImplementedError

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
        shutil.copy2(self.currentFile(),
                     os.path.join(directory, bidsname + ext))

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
        return os.path.join(destination, self.currentFile(False))

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
        if prefix != "":
            logger.warning("{}/{}: Undefined field prefix {}"
                           .format(self.Module(),
                                   self.Type(),
                                   prefix))
        return value

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
        if not os.path.isfile(file):
            raise FileNotFoundError("File {} not found or not a file"
                                    .format(file))
        if not os.access(file, os.R_OK):
            raise PermissionError("File {} not readable"
                                  .format(file))
        return cls._isValidFile(file)

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
        field = field.split(prefix, 1)
        if len(field) == 2:
            prefix, field = field
        else:
            prefix = ""
            field = field[0]
        result = self._getField(field.split(separator))

        if result is None:
            return default
        if prefix != "":
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
                        cleanup: bool = True, raw: bool = False):
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
                    if result is None:
                        logger.warning("{}: Can't find '{}' "
                                       "attribute from '{}'"
                                       .format(self.recIdentity(),
                                               query, field))
                        result = query
                else:
                    prefix = ""
                    if ":" in query:
                        prefix, query = query.split(":", 1)
                    if prefix == "":
                        result = self._getCharacteristic(query)
                    elif prefix == "bids":
                        result = self.labels[query]
                    elif prefix == "sub_tsv":
                        result = self.sub_BIDSvalues[query]
                    elif prefix == "rec_tsv":
                        result = self.sub_BIDSvalues[query]
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
        self._bidsSession = session
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
            logger.error("{}/{}: Unable to determine session Id from {}"
                         .format(self.recNo(), self.recId(),
                                 name))
            raise ValueError("Invalid session Id")
        self._bidsSession.unlock_session()
        self._bidsSession.session = subid
        self._bidsSession.lock_session()

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
        self.index = index
        for key in self.attributes:
            self.attributes[key] = self.getField(key)

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

        with open(os.path.join(outdir, bidsname + ".json"), "w") as f:
            js_dict = self.exportMeta()
            json.dump(js_dict, f, indent=2)

        self.rec_BIDSvalues["filename"] = os.path.join(self.Modality(),
                                                       bidsname
                                                       + ext)
        self.rec_BIDSvalues["acq_time"] = self.acqTime()\
            .replace(microsecond=0)

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

        self._suffix = ""
        self._modality = unknownmodality
        self.labels = OrderedDict()
        if not run:
            return

        if run.modality in self.bidsmodalities:
            self._modality = run.modality
            tags = set(self.bidsmodalities[run.modality]) \
                - set(run.entity)
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

    def generateMeta(self):
        """
        Fills standard meta values. Must be called before exporting
        these meta-data into json
        """
        if not self._modality:
            logger.error("{}/{}: Modality not defined"
                         .format(self.Module(), self.Type()))
            raise ValueError("Modality wasn't defined")

        for key, field in self.metaFields.items():
            if field is not None:
                if field.name.startswith("<"):
                    field.value = self.getDynamicField(field.name,
                                                       field.default)
                else:
                    field.value = self.getField(field.name, field.default)

    def exportMeta(self):
        """
        Exports recording metadata into dictionary structure
        """
        exp = dict()
        for key, field in self.metaAuxiliary.items():
            if field:
                if isinstance(field, list):
                    exp[key] = [f.value for f in field]
                else:
                    exp[key] = field.value
        for key, field in self.metaFields.items():
            if field:
                if key not in self.metaAuxiliary:
                    if isinstance(field, list):
                        exp[key] = [f.value for f in field]
                    else:
                        exp[key] = field.value
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
                         .format(self.Module(),
                                 self.Type()))
            return False
        match_one = False
        match_all = True
        for attrkey, attrvalue in run.attribute.items():
            if not attrvalue:
                continue
            res = self.matchAttribute(attrkey, attrvalue)
            match_one = match_one or res
            match_all = match_all and res
            if not match_all:
                break
        return match_one and match_all
