from bidsme.Modules import baseModule
from bidsme.Modules.common import retrieveFormDict

class testModule(baseModule):
    _module = "TEST"
    _type = "testModule"

    def __init__(self):
        super().__init__()

        self._HEADER_CACHE = None
        self._FILE_CACHE = ""
        self._header_file = ""

    @classmethod
    def _isValidFile(cls, file: str) -> bool:
        return True

    def _loadFile(self, path: str) -> None:
        self._FILE_CACHE = {}

    def _getAcqTime(self):
        return None

    def dump(self):
        return ""

    def _getField(self, field: list):
        return retrieveFormDict(field, self._HEADER_CACHE,
                                fail_on_last_not_found=False)

    def _recNo(self):
        return None

    def _recId(self):
        return None

    def isCompleteRecording(self):
        return True

    def _getSubId(self):
        return "unknown"

    def _getSesId(self):
        return "unknown"
