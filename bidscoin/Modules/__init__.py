from . import MRI
from .selector import types_list, select, selectFile, selectByName
from ._constants import ignoremodality, unknownmodality

# from .selector import select, selectFile, selectByName
# types_list = {"MRI": (MRI.DICOM, MRI.Nifti_SPM12)}

__all__ = ["types_list", "select", "selectFile", "selectByName",
           "ignoremodality", "unknownmodality"]
