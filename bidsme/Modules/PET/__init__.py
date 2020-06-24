from .bidsmeNIFTI import bidsmeNIFTI
from .NIFTI import NIFTI

try:
    from .DICOM import DICOM
except ModuleNotFoundError as e:
    if e.name == "pydicom":
        from .._formats.dummy import dummy as DICOM
        DICOM.classes["DICOM"] = e.name
    else:
        raise

try:
    from .ECAT import ECAT
except ModuleNotFoundError as e:
    if e.name == "nibabel":
        from .._formats.dummy import dummy as ECAT
        DICOM.classes["ECAT"] = e.name
    else:
        raise


__all__ = ["DICOM", "ECAT", "bidsmeNIFTI", "NIFTI"]
