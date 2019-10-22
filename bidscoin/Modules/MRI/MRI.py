import logging


logger = logging.getLogger(__name__)

class MRI(object):
    __slots__ = ["type", "bidsmodalities",
                 "bidslabels",
                 "index",
                 "files",
                 "type",
                 "acq_path"]

    def __init__(self, acq_path: str = ""):
        self.name = "MRI"
        self.bidsmodalities = ('fmap', 'anat', 'func', 'dwi', 'beh', 'pet')
        self.bidslabels = ('task', 'acq', 'ce', 'rec', 'dir', 'run', 'mod',
                           'echo', 'suffix', 'IntendedFor')
        self.type = "None"
        self.files = list()
        self.acq_path = ""
        self.index = -1
        
        self.set_acq_path(acq_path)

    def isValidFile(self, file: str) -> bool:
        raise NotImplementedError

    def loadFile(self, index: int) -> None:
        raise NotImplementedError

    def get_field(self, field: str):
        raise NotImplemented

    def loadNextFile(self) -> bool:
        if self.index + 1 >= len(self.files):
            return False
        self.loadFile(self.index + 1)

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

    def set_rec_path(self, rec_path:str) -> int:
        """
        Set given folder as folder containing all files fron given recording.
        Returns number of valid files in folder.
        Clears all current files in cashe.

        :rec_path:  The full path name to the folder
        :return:    Number of valid files
        """
        if not os.isdir(rec_path):
            raise NotADirectoryError("Path {} is not a folder"
                                     .format(rec_path))
        self.rec_path = rec_path
        self.clearCache()
        self.files = clear()

        for file in sorted(os.listdir(self.rec_path)):
            if os.path.basename(file).startswith('.'):
                logger.warning(f'Ignoring hidden file: {file}')
                continue
            full_path = os.path.join(folder, file)
            if self.isValidFile(full_path):
                    self.files.append(full_path)
        if len(self.files) == 0:
            logger.warning("No valid {} files found in {}"
                           .format(self.type, self.rec_path))
        logger.debug("Found {} files in {}"
                     .format(len(self.files), self.rec_path))
        return len(self.files)


