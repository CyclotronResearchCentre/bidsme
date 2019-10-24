import os
import logging

from tools import tools

logger = logging.getLogger(__name__)


class MRI(object):
    __slots__ = [
                 "index",
                 "files",
                 "type",
                 "rec_path"]

    bidsmodalities = ('fmap', 'anat', 'func', 'dwi', 'beh', 'pet')
    bidslabels = ('task', 'acq', 'ce', 'rec', 'dir', 'run', 'mod',
                  'echo', 'suffix', 'IntendedFor')
    def __init__(self):
        self.type = "None"
        self.files = list()
        self.rec_path = ""
        self.index = -1

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

    def get_field(self, field: str):
        raise NotImplemented

    def get_dynamic_field(self, field: str):
        val = field
        if not field or not isinstance(field, str) or\
                field.startswith('<<'):
            return field
        if field.startswith('<') and field.endswith('>'):
            val = self.get_field(field[1:-1])
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

    def currentFile(self):
        if self.index >= 0 and self.index < len(self.files):
            return self.files[self.index]
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
        self.rec_path = rec_path
        self.clearCache()
        self.files.clear()

        for file in sorted(os.listdir(self.rec_path)):
            if os.path.basename(file).startswith('.'):
                logger.warning(f'Ignoring hidden file: {file}')
                continue
            full_path = os.path.join(self.rec_path, file)
            if self.isValidFile(full_path):
                    self.files.append(full_path)
        if len(self.files) == 0:
            logger.warning("No valid {} files found in {}"
                           .format(self.type, self.rec_path))
        else:
            self.loadFile(0)
        logger.debug("Found {} files in {}"
                     .format(len(self.files), self.rec_path))
        return len(self.files)
