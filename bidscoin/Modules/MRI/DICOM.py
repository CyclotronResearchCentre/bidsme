from Modules.MRI.MRI import MRI

import os
import re
import logging
import pydicom

logger = logging.getLogger(__name__)


class DICOM(MRI):
    __slots__ = ["_DICOMDICT_CACHE", "_DICOMFILE_CACHE", "isSiemens"]

    def __init__(self, recording=""):
        super().__init__()

        self._DICOMDICT_CACHE = None
        self._DICOMFILE_CACHE = ""
        self.isSiemens = False
        self.type = "DICOM"
        self.converter = "dcm2niix"

        if recording:
            self.set_rec_path(recording)

    @classmethod
    def isValidFile(cls, file: str) -> bool:
        """
        Checks whether a file is a DICOM-file. It uses the feature
        that Dicoms have the string DICM hardcoded at offset 0x80.

        :param file:    The full pathname of the file
        :return:        Returns true if a file is a DICOM-file
        """

        if os.path.isfile(file):
            if os.path.basename(file).startswith('.'):
                logger.warning(f'DICOM file is hidden: {file}')
            with open(file, 'rb') as dcmfile:
                dcmfile.seek(0x80, 1)
                if dcmfile.read(4) == b'DICM':
                    return True
                else:
                    # The DICM tag may be missing for anonymized DICOM files
                    dicomdict = pydicom.dcmread(file, force=True)
                    return 'Modality' in dicomdict
        else:
            return False

    def convert(self, destination: str, options: dict) -> bool:
        if self.converter not in options:
            raise ValueError("Missing configuration options for {}"
                             .format(self.converter))
        options = options['dcm2niix']
        command = '{path}dcm2niix {args} -f "{filename}" '\
                  '-o "{outfolder}" "{infolder}"'\
                  .format(path=options['path'],
                          args=options['args'],
                          filename=self.get_bidsname(),
                          outfolder=destination,
                          infolder=self.rec_path)

        if not bids.run_command(command):
            return False
        return True

    def loadFile(self, index: int) -> None:
        path = self.files[index]
        if not self.isValidFile(self, path):
            raise ValueError("{} is not valid {} file"
                             .format(path, self.name))
        if path != self._DICOMFILE_CACHE:
            # The DICM tag may be missing for anonymized DICOM files
            dicomdict = pydicom.dcmread(path, force=True)
            self._DICOMFILE_CACHE = path
            self._DICOMDICT_CACHE = dicomdict
            self.isSiemens = self.is_dicomfile_siemens(self._DICOMFILE_CACHE)
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

    def parse_x_protocol(self, pattern: str) -> str:
        """
        Siemens writes a protocol structure as text into each DICOM file.
        This structure is necessary to recreate a scanning protocol
        from a DICOM, since the DICOM information alone
        wouldn't be sufficient.

        :param pattern:     A regexp expression:
                            '^' + pattern + '\t = \t(.*)\\n'
        :return:            The string extracted values from the dicom-file
                            according to the given pattern
        """
        if not self.isSiemens:
            logger.warning('Parsing {} may fail because {} does not seem '
                           'to be a Siemens DICOM file'
                           .format(pattern, self.file))
        regexp = '^' + pattern + '\t = \t(.*)\n'
        regex = re.compile(regexp.encode('utf-8'))
        with open(self.file, 'rb') as openfile:
            for line in openfile:
                match = regex.match(line)
                if match:
                    return match.group(1).decode('utf-8')
        logger.warning("Pattern: '{}' not found in {}"
                       .format(regexp.encode('unicode_escape').decode(),
                               self.file))
        return None

    def is_dicomfile_siemens(file: str) -> bool:
        """
        Checks whether a file is a *SIEMENS* DICOM-file.
        All Siemens Dicoms contain a dump of the  MrProt structure.
        The dump is marked with a header starting with 'ASCCONV BEGIN'.
        Though this check is not foolproof, it is very unlikely to fail.

        :param file:    The full pathname of the file
        :return:        Returns true if a file is a Siemens DICOM-file
        """
        return b'ASCCONV BEGIN' in open(file, 'rb').read()

    def isComplete(self):
        nrep = self.get_field('lRepetitions')
        nfiles = self.get_nFiles()

        if nrep and nrep > nfiles:
            logger.warning('{}: Incomplete acquisition: '
                           '\nExpected {}, found {} dicomfiles'
                           .format(self._DICOMFILE_CACHE, nrep, nfiles))
            return False
        return True
