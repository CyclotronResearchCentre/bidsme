from Modules.MRI.MRI import MRI

import os
import logging
import json
import pprint

logger = logging.getLogger(__name__)


class Nifti_dump(MRI):
    __slots__ = ["_DICOMDICT_CACHE", "_DICOMFILE_CACHE","isSiemens"]

    def __init__(self, bidsmap=None, rec_path=""):
        super().__init__()

        self._DICOMDICT_CACHE = None
        self._DICOMFILE_CACHE = ""
        self.isSiemens = False
        self.type = "Nifti_dump"

        if rec_path:
            self.set_rec_path(rec_path)
        if bidsmap:
            self.set_attributes(bidsmap)

    def dump(self):
        if self._DICOMDICT_CACHE:
            return pprint.pformat(self._DICOMDICT_CACHE,
                                  indent=2, width=40, compact=True)
        elif len(self.files) > 0:
            self.loadFile(0)
            return pprint.pformat(self._DICOMDICT_CACHE, 
                                  indent=2, width=40, compact=True)
        else:
            logger.error("No defined files")
            return "No defined files"

    @classmethod
    def isValidFile(cls, file: str) -> bool:
        """
        Checks whether a file is a NII file with a valid json dump,
        produced by SPM12

        :param file:    The full pathname of the file
        :return:        Returns true if a file is a DICOM-file
        """

        if os.path.isfile(file) and file.endswith(".nii"):
            if os.path.basename(file).startswith('.'):
                logger.warning(f'NII_DUMP file is hidden: {file}')
            try:
                acqpar = cls.__loadJsonDump(file)
            except Exception as e:
                logger.warning("File {}: {}".format(file, str(e)))
                return False
            if "Modality" in acqpar:
                return True
            else :
                logger.warning("File {}: missing 'Modality' "
                               "in acquisition parameters"
                               .format(file))
                return False
        else:
            return False

    @staticmethod
    def __loadJsonDump(file: str) -> dict:
        json_dump = file[:-4] + ".json"
        with open(json_dump, "r") as f:
            return json.load(f)["acqpar"][0]

    def loadFile(self, index: int) -> None:
        path = os.path.join(self.rec_path,self.files[index])
        if not self.isValidFile(path):
            raise ValueError("{} is not valid {} file"
                             .format(path, self.name))
        if path != self._DICOMFILE_CACHE:
            # The DICM tag may be missing for anonymized DICOM files
            dicomdict = self.__loadJsonDump(path)
            self._DICOMFILE_CACHE = path
            self._DICOMDICT_CACHE = dicomdict
            self.isSiemens = (self._DICOMDICT_CACHE["Manufacturer"]
                              == "SIEMENS ")
            for key in self.attributes:
                self.attributes[key] = self.get_field(key)
        self.index = index

    def get_field(self, field: str):
        try:
            value = self._DICOMDICT_CACHE.get(field)
            if not value:
                for elem in self._DICOMDICT_CACHE.iterall():
                    if elem.name == field:
                        value = elem.value
                        continue
        except Exception: 
            logger.warning("Could not parse {} from {}"
                           .format(field, self._DICOMFILE_CACHE))
            value = None

        if not value:
            return ""
        elif isinstance(value, int):
            return int(value)
        else:
            return str(value)

    def clearCache(self) -> None:
        self._DICOMDICT_CACHE = None
        self._DICOMFILE_CACHE = ""

    def isComplete(self):
        return True
