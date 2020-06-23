try:
    from .DICOM import DICOM
except ModuleNotFoundError as e:
    if e.name == "pydicom":
        from .._formats.dummy import dummy as DICOM
        DICOM.classes["DICOM"] = e.name
    else:
        raise

from .hmriNIFTI import hmriNIFTI
from .bidsmeNIFTI import bidsmeNIFTI
from .jsonNIFTI import jsonNIFTI
from .NIFTI import NIFTI

__all__ = ["DICOM", "hmriNIFTI", "bidsmeNIFTI", "jsonNIFTI", "NIFTI"]
