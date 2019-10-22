from Modules.MRI import MRI

import os
import logging

logger = logging.getLogger(__name__)

class NII_DUMP(MRI):
    __slots__ = ["_DICOMDICT_CACHE", "_DICOMFILE_CACHE","isSiemens"]

    def __init__(self, index=None):
        super(NII_DUMP, self).__init__()

        self._DICOMDICT_CACHE = None
        self._DICOMFILE_CACHE = ""
        self.isSiemens = False
        self.type = "NII_DUMP"

        if index is not None:
            self.loadFile(index)


    def isValidFile(self, file: str) -> bool:
        """
        Checks whether a file is a NII file with a valid json dump,
        produced by SPM12

        :param file:    The full pathname of the file
        :return:        Returns true if a file is a DICOM-file
        """

        if os.path.isfile(file) and file.endswith(".nii"):
            if os.path.basename(file).startswith('.'):
                logger.warning(f'{self.type} file is hidden: {file}')
            try:
                acqpar = self.__loadJsonDump(file)
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

    def __loadJsonDump(self, file: str) -> dict:
        json_dump = file[:-4] + ".json"
        with open(json_dump, "r") as f:
            return json.load(f)["acqpar"][0]


    def loadFile(self, index: int) -> None:
        path = self.files[index]
        if not self.isValidFile(self, path):
            raise ValueError("{} is not valid {} file"
                             .format(path, self.name))
        if path != self._DICOMFILE_CACHE
            # The DICM tag may be missing for anonymized DICOM files
            dicomdict = self.__loadJsonDump(path)
            self._DICOMFILE_CACHE = path
            self._DICOMDICT_CACHE = dicomdict
            self.isSiemens = (self._DICOMDICT_CACHE["Manufacturer"] == "SIEMENS ")
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
            try: 
                value = self.parse_x_protocol(field)
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
