import os
import logging
import re
from datetime import datetime
from collections import OrderedDict

from tools import tools
from bidsMeta import MetaField
from bidsMeta import BIDSfieldLibrary

logger = logging.getLogger(__name__)

mri_meta_required = [
        # funct specific
        "RepetitionTime", "VolumeTiming", "TaskName",
        # fmap specific
        "IntendedFor"
        ]

mri_meta_recommended = [
        # Scanner hardware
        "Manufacturer", "ManufacturersModelName", "DeviceSerialNumber",
        "StationName", "SoftwareVersions",
        "MagneticFieldStrength", "ReceiveCoilName",
        "ReceiveCoilActiveElements",
        "GradientSetType", "MRTransmitCoilSequence",
        "MatrixCoilMode", "CoilCombinationMethod",
        # Sequence Specifics
        "PulseSequenceType", "ScanningSequence", "SequenceVariant",
        "ScanOptions", "SequenceName", "PulseSequenceDetails",
        "NonlinearGradientCorrection",
        # In-Plane Spatial Encoding
        "NumberShots", "ParallelReductionFactorInPlane",
        "ParallelAcquisitionTechnique", "PartialFourier",
        "PartialFourierDirection", "PhaseEncodingDirection",
        "EffectiveEchoSpacing", "TotalReadoutTime",
        # Timing Parameters
        "EchoTime", "InversionTime", "SliceTiming",
        "SliceEncodingDirection", "DwellTime",
        # RF & Contrast
        "FlipAngle", "MultibandAccelerationFactor",
        # Slice Acceleration
        "MultibandAccelerationFactor",
        # Anatomical landmarks
        "AnatomicalLandmarkCoordinates",
        # Institution information
        "InstitutionName", "InstitutionAddress", "InstitutionalDepartmentName",
        # funct specific
        "NumberOfVolumesDiscardedByScanner", "NumberOfVolumesDiscardedByUser",
        "DelayTime", "AcquisitionDuration", "DelayAfterTrigger",
        "Instructions", "TaskDescription", "CogAtlasID", "CogPOID"
        ]

mri_meta_optional = [
        # RF & Contrast
        "NegativeContrast",
        # anat specific
        "ContrastBolusIngredient",

        ]


class MRI(object):
    __slots__ = [
                 "modality",
                 "Subject", "Session",
                 "attributes", "labels", "suffix",
                 "main_attributes",
                 "index", "files", "rec_path",
                 "type", "converter",
                 "metaAuxiliary",
                 "metaFields",
                 "rec_BIDSvalues",
                 "sub_BIDSvalues"
                 ]
    Module = "MRI"

    bidsmodalities = {
            "anat": ("acq", "ce", "rec", "mod", "run"),
            "func": ("task", "acq", "ce", "dir", "rec", "run", "echo"),
            "dwi": ("acq", "dir", "run"),
            "fmap": ("acq", "ce", "dir", "run"),
            "beh": ("task")
            }

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
        self.type = "None"
        self.converter = None
        self.files = list()
        self.rec_path = ""
        self.index = -1
        self.attributes = dict()
        self.labels = OrderedDict()
        self.suffix = ""
        self.modality = self.unknownmodality
        self.Subject = "<<SourceFilePath>>"
        self.Session = "<<SourceFilePath>>"
        self.main_attributes = set()

        self.metaFields = {key: None for key in
                           mri_meta_required
                           + mri_meta_recommended
                           + mri_meta_optional}
        self.metaAuxiliary = dict()
        self.rec_BIDSvalues = dict()
        self.sub_BIDSvalues = dict()

    @classmethod
    def isValidRecording(cls, rec_path: str) -> bool:
        for file in os.listdir(rec_path):
            if cls.isValidFile(os.path.join(rec_path, file)):
                return True
        return False

    @classmethod
    def isValidModality(cls, modality: str,
                        include_unknown: bool = True) -> bool:
        passed = False
        if include_unknown and modality == cls.ignoremodality:
            passed = True
        if modality in cls.bidsmodalities:
            passed = True
        return passed

    @classmethod
    def isValidFile(cls, file: str) -> bool:
        raise NotImplementedError

    @classmethod
    def get_type(cls):
        raise NotImplementedError

    def clearCache(self) -> None:
        pass

    def loadFile(self, index: int) -> None:
        raise NotImplementedError

    def acq_time(self) -> datetime:
        raise NotImplementedError

    def dump(self):
        return NotImplementedError

    def get_field(self, field: str):
        raise NotImplementedError

    def convert(self, destination, config: dict) -> bool:
        raise NotImplementedError

    def copy_file(self, destination) -> None:
        raise NotImplementedError

    def get_attribute(self, attribute: str):
        if attribute in self.attributes:
            return self.attributes[attribute]
        else:
            res = self.get_field(attribute)
            if res:
                self.attributes[attribute] = res
            return res

    def get_dynamic_field(self, field: str, cleanup=True):
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
                    result = self.get_attribute(query)
                else:
                    if query.startswith("bids:"):
                        result = self.labels[len("bids:"):]
                    elif query.startswith("sub_tsv:"):
                        result = self.sub_BIDSvalues[len("sub_tsv:"):]
                    elif query.startswith("rec_tsv:"):
                        result = self.sub_BIDSvalues[len("rec_tsv:"):]
                    else:
                        result = self._getCharacteristic(query)
                if result is None:
                    raise KeyError("Cant interpret {} at {} from {}"
                                   .format(query, pos, field))
                res += str(result)
                start = pos2 + len(seek)
            except Exception as e:
                logger.error("Malformed field '{}': {}".format(field, str(e)))
                raise

        if cleanup:
            res = tools.cleanup_value(res)

        return res

    def get_rec_no(self):
        return self.get_field("SeriesNumber")

    def get_rec_id(self):
        seriesdescr = self.get_field("SeriesDescription")
        if not seriesdescr:
            seriesdescr = self.get_field("ProtocolName")
        if not seriesdescr:
            logger.warning("Unable to get recording Id for file {}"
                           .format(self.currentFile()))
            seriesdescr = "unknown"
        return seriesdescr

    def loadNextFile(self) -> bool:
        if self.index + 1 >= len(self.files):
            return False
        self.loadFile(self.index + 1)
        return True

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

    def get_file(self, folder: str, index: int = 0) -> str:
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
                return os.path.join(self.rec_path, self.files[self.index])
        return None

    def set_rec_path(self, rec_path: str) -> int:
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
        if bidsmap:
            for mod in list(self.bidsmodalities) + [self.ignoremodality]:
                if mod in bidsmap and bidsmap[mod]:
                    for run in bidsmap[mod]:
                        for attkey in run['attributes']:
                            if self.index >= 0:
                                self.attributes[attkey] = \
                                        self.get_field(attkey)

    def set_main_attributes(self, run):
        if run:
            self.main_attributes = [attkey
                                    for attkey, attval
                                    in run.attribute.items()
                                    if attval]
        else:
            self.main_attributes = []

    def set_labels(self, run=None):
        self.suffix = ""
        self.modality = self.unknownmodality
        self.labels = OrderedDict()
        if not run:
            return

        if run.modality in self.bidsmodalities:
            self.modality = run.modality
            tags = set(self.bidsmodalities[run.modality]) \
                - set(run.entity)
            if tags:
                logger.warning("Naming scheema do not follow BIDS standard")
                self.labels = OrderedDict.fromkeys(run.entity)
            else:
                self.labels = OrderedDict.fromkeys(
                        self.bidsmodalities[run.modality])
            self.suffix = self.get_dynamic_field(run.suffix)
            for key in run.entity:
                val = self.get_dynamic_field(run.entity[key])
                self.labels[key] = val
        elif run.modality == self.ignoremodality:
            self.modality = run.modality
        else:
            logger.error("{}/{}: Unregistered modality {}"
                         .format(self.get_rec_id(), self.index))

        self.metaAuxiliary = dict()
        for key, val in run.json.items():
            if key and run.json[key]:
                if isinstance(val, list):
                    self.metaAuxiliary[key] = [
                            MetaField(key, "",
                                      self.get_dynamic_field(v, False))
                            for v in val]
                else:
                    self.metaAuxiliary[key] = MetaField(
                            key, "",
                            self.get_dynamic_field(val, False))

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
        for attrkey, attrvalue in run.attribute.items():
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
        elif self.Subject.startswith("<<"):
            if self.Subject == '<<SourceFilePath>>':
                subid = self.get_id_folder("sub-")
            else:
                raise ValueError("Illegal field value: {}"
                                 .format(self.Subject))
        else:
            subid = self.get_dynamic_field(self.Subject)
        return 'sub-' + tools.cleanup_value(re.sub('^sub-', '', subid))

    def getSesId(self):
        if self.Session == "":
            return ""
        elif self.Session.startswith("<<"):
            if self.Session == '<<SourceFilePath>>':
                subid = self.get_id_folder("ses-")
            else:
                raise ValueError("Illegal field value: {}"
                                 .format(self.Session))
        else:
            subid = self.get_dynamic_field(self.Session)
        ses = tools.cleanup_value(re.sub('^ses-', '', subid))
        if ses == "":
            return ses
        else:
            return 'ses-' + ses

    def get_bidsname(self):
        tags_list = list()
        subid = self.getSubId()
        if subid:
            tags_list.append(subid)
        sesid = self.getSesId()
        if sesid:
            tags_list.append(sesid)
        for key, val in self.labels.items():
            if val:
                tags_list.append(key + "-"
                                 + tools.cleanup_value(val))

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
                        subprefix: str = "sub-",
                        sesprefix: str = "ses-"):
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

    def generateMeta(self):
        if not self.modality:
            raise ValueError("Modality wasn't defined")

        for key, field in self.metaFields.items():
            if field and field.name:
                field.value = self.get_field(field.name)

    def exportMeta(self):
        exp = dict()
        for key, field in self.metaAuxiliary.items():
            if field:
                if isinstance(field, list):
                    exp[key] = [f.value for f in field]
                else:
                    exp[key] = field.value
        for key, field in self.metaFields.items():
            if field and key not in self.metaAuxiliary:
                if isinstance(field, list):
                    exp[key] = [f.value for f in field]
                else:
                    exp[key] = field.value
        return exp

    def _getCharacteristic(self, field):
        if field == "subject":
            return self.getSubId()
        if field == "session":
            return self.getSesId()
        if field == "serieNumber":
            return self.get_rec_no()
        if field == "serie":
            return self.get_rec_id()
        if field == "count":
            return self.index + 1
        if field == "nfiles":
            return len(self.files)
        if field == "filename":
            return self.currentFile(False)
        if field == "suffix":
            return self.suffix
        if field == "modality":
            return self.modality
        if field == "module":
            return self.Module
