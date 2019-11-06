import os
import logging
import re

from tools import tools

logger = logging.getLogger(__name__)


class MRI(object):
    __slots__ = [
                 "modality",
                 "Subject", "Session",
                 "attributes", "labels", "suffix", 
                 "main_attributes",
                 "index", "files", "rec_path",
                 "type",
                 ]
    Module = "MRI"

    bidsmodalities = {
            "anat" : ("acq", "ce", "rec", "mod", "run"),
            "func" : ("task", "acq", "ce", "dir", "rec", "run", "echo"),
            "dwi"  : ("acq", "dir", "run"),
            "fmap" : ("acq", "ce", "dir", "run"),
            "beh"  : ("task")
            }

    ignoremodality = '__ignore__'
    unknownmodality = '__unknown__'

    def __init__(self, bidsmap=None, rec_path=""):
        self.type = "None"
        self.files = list()
        self.rec_path = ""
        self.index = -1
        self.attributes = dict()
        self.labels = list()
        self.suffix = ""
        self.modality = ""
        self.Subject = "<<SourceFilePath>>"
        self.Session = "<<SourceFilepath>>"
        self.main_attributes = set()

    @classmethod
    def isValidRecording(cls, rec_path: str) -> bool:
        for file in os.listdir(rec_path):
            if cls.isValidFile(os.path.join(rec_path,file)):
                return True
        return False

    @classmethod
    def isValidFile(cls, file: str) -> bool:
        raise NotImplementedError

    def clearCache(self) -> None:
        pass

    def loadFile(self, index: int) -> None:
        raise NotImplementedError

    def dump(self):
        return NotImplementedError

    def get_field(self, field: str):
        raise NotImplemented

    def get_attribute(self, attribute: str):
        if attribute in self.attributes:
            return self.attributes[attribute]
        else:
            res = self.get_field(attribute)
            if res:
                self.attributes[attribute] = res
            return res

    def get_dynamic_field(self, field: str):
        val = field
        if not field or not isinstance(field, str) or\
                field.startswith('<<'):
            return field
        if field.startswith('<') and field.endswith('>'):
            val = self.get_attribute(field[1:-1])
            if not val:
                return field
            else:
                val = tools.cleanup_value(val)
        return val

    def loadNextFile(self) -> bool:
        if self.index + 1 >= len(self.files):
            return False
        self.loadFile(self.index + 1)

    def isComplete(self):
        raise NotImplementedError

    def get_nFiles(self, folder: str) -> int:
        """
        Return number of valid files in folder

        :param folder:  The full pathname of the folder
        :return:        Number of valid files
        """
        count = 0
        for file in os.listdir(folder):
            if os.path.basename(file).startswith('.'):
                logger.warning(f'Ignoring hidden file: {file}')
                continue
            full_path = os.path.join(folder, file)
            if self.isValidFile(full_path):
                    count += 1
        return count

    def get_file(self, folder: str, index: int=0) -> str:
        """
        Return the valid file of index from folder without loading
        correwsponding folder. If you wnat to load folder, use 
        set_rec_path instead

        :param folder:  The full pathname of the folder
        :index:         The index number of the file
        :return:        The filename of the first valid file in the folder.
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
        logger.warning(f'Cannot find >{index} {self.type} files in: {folder}')
        return None

    def currentFile(self, base=False):
        if self.index >= 0 and self.index < len(self.files):
            if base:
                return self.files[self.index]
            else:
                return os.path.join(self.rec_path,self.files[self.index])
        return None

    def set_rec_path(self, rec_path:str) -> int:
        """
        Set given folder as folder containing all files fron given recording.
        Returns number of valid files in folder.
        Clears all current files in cashe.

        :rec_path:  The full path name to the folder
        :return:    Number of valid files
        """
        if not os.path.isdir(rec_path):
            raise NotADirectoryError("Path {} is not a folder"
                                     .format(rec_path))
        self.rec_path = os.path.normpath(rec_path)
        self.clearCache()
        self.files.clear()

        for file in sorted(os.listdir(self.rec_path)):
            if os.path.basename(file).startswith('.'):
                logger.warning(f'Ignoring hidden file: {file}')
                continue
            full_path = os.path.join(self.rec_path, file)
            if self.isValidFile(full_path):
                    self.files.append(file)
        if len(self.files) == 0:
            logger.warning("No valid {} files found in {}"
                           .format(self.type, self.rec_path))
        else:
            self.loadFile(0)
        logger.debug("Found {} files in {}"
                     .format(len(self.files), self.rec_path))
        return len(self.files)

    def set_attributes(self, bidsmap) -> None:
        self.attributes = dict()
        if bidsmap is not None:
            for modality in bidsmap:
                if bidsmap[modality] and \
                        isinstance(bidsmap[modality], list):
                    for run in bidsmap[modality]:
                        for attkey in run['attributes']:
                            if self.index >= 0:
                                self.attributes[attkey] = \
                                        self.get_field(attkey)

    def set_main_attributes(self, run: dict):
        self.main_attributes = [attkey 
                                for attkey, attval 
                                in run['attributes'].items()
                                if attval]

    def set_labels(self, modality, run=dict()):
        self.suffix = ""
        self.modality = ""
        self.labels = list()
        if not modality:
            return
        run = run["bids"]
        self.suffix = run["suffix"]
        if modality in self.bidsmodalities:
            self.labels = [""] * len(self.bidsmodalities[modality])
            for index, key in enumerate(self.bidsmodalities[modality]):
                if key in run and run[key]:
                    val = self.get_dynamic_field(run[key])
                    if isinstance(val, str):
                        if val.lower().endswith(self.suffix.lower()):
                            val = val[:-len(self.suffix)]
                    self.labels[index] = val

            self.modality = modality
        elif modality == self.ignoremodality:
                self.modality = modality
        else:
            self.modality = self.unknownmodality

    def match_attribute(self, attribute, pattern) -> bool:
        if not pattern:
            return True
        attval = self.get_attribute(attribute)
        if isinstance(pattern, list):
            for val in pattern:
                if tools.match_value(attval, val):
                    return True
            return False
        return tools.match_value(attval, pattern)

    def match_run(self, run):
        if run is None:
            logger.debug("{}: trying to match empty runs"
                         .format(self.type))
            return False
        match_one = False
        match_all = True
        for attrkey, attrvalue in run['attributes'].items():
            if not attrvalue:
                continue
            res = self.match_attribute(attrkey, attrvalue)
            match_one = match_one or res
            match_all = match_all and res
            if not match_all:
                break
        return match_one and match_all

    def getSubId(self):
        if self.Subject == "":
            return ""
        elif self.Subject == '<<SourceFilePath>>':
            subid = self.get_id_folder("sub-")
        else:
            subid = self.get_dynamic_field(self.Subject)
        return 'sub-' + tools.cleanup_value(re.sub('^sub-', '', subid))

    def getSesId(self):
        if self.Session == "":
            return ""
        elif self.Session == '<<SourceFilePath>>':
            subid = self.get_id_folder("ses-")
        else:
            subid = self.get_dynamic_field(self.Session)
        return 'sub-' + tools.cleanup_value(re.sub('^sub-', '', subid))

    def get_bidsname(self):
        tags_list = list()
        subid = self.getSubId()
        if subid:
            tags_list.append(subid)
        sesid = self.getSesId()
        if sesid:
            tags_list.append(sesid)
        for key in self.bidsmodalities[self.modality]:
            if key in self.labels and self.labels[key]:
                tags_list.append(key + "-" 
                                 + tools.cleanup_value(self.labels[key]))

        if self.suffix:
            tags_list.append(tools.cleanup_value(self.suffix))
        return "_".join(tags_list)

    def get_id_folder(self, prefix: str):
        if self.rec_path == "":
            logger.error("Recording path not defined")
            return

        # recording path means to be organized as 
        # ..../sub-xxx/[ses-yyy]/sequence/files
        try:
            subid = self.rec_path.rsplit("/" + prefix, 1)[1]\
                    .split(os.sep)[0]
        except Exception:
            raise ValueError("Failed to extract '{}' form {}"
                             .format(prefix, self.rec_path))
        return subid

    def set_subid_sesid(self, subid: str, sesid: str,
                        subprefix: str="sub-",
                        sesprefix: str="ses-"):
        """
        Extract the cleaned-up subid and sesid from the pathname 
        or from the dicom file if subid/sesid == '<<SourceFilePath>>'

        :param subid:       The subject identifier, 
                            i.e. name of the subject folder 
                            (e.g. 'sub-001' or just '001'). Can be left empty
        :param sesid:       The optional session identifier, 
                            i.e. name of the session folder 
                            (e.g. 'ses-01' or just '01')
        :return:            Updated (subid, sesid) tuple,
                            including the sub/sesprefix
        """
        # Add default value for subid and sesid (e.g. for the bidseditor)
        if subid == "":
            raise ValueError("{}: subid value must be non-empty")
        if subid == '<<SourceFilePath>>':
            subid = self.get_id_folder("sub-")
        else:
            subid = self.get_dynamic_field(subid)
        if sesid: 
            if sesid == '<<SourceFilePath>>':
                sesid = self.get_id_folder("ses-")
            else:
                sesid = self.get_dynamic_value(sesid)
        # Add sub- and ses- prefixes if they are not there
        self.sub = 'sub-' + tools.cleanup_value(
                re.sub('^sub-', '', subid))
        if sesid:
            self.ses = 'ses-' + tools.cleanup_value(
                     re.sub('^ses-', '', sesid))
        else:
            self.ses = ''
