from .bidsmeNIFTI import bidsmeNIFTI
from .NIFTI import NIFTI

try:
    from .DICOM import DICOM
except ModuleNotFoundError as e:
    from .._formats.dummy import dummy as DICOM
    DICOM.classes["DICOM"] = e.name

try:
    from .ECAT import ECAT
except ModuleNotFoundError as e:
    from .._formats.dummy import dummy as ECAT
    ECAT.classes["ECAT"] = e.name


__all__ = ["DICOM", "ECAT", "bidsmeNIFTI", "NIFTI"]

__formats = [DICOM, ECAT, bidsmeNIFTI, NIFTI]
