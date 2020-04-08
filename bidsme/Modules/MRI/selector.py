from Modules.MRI.DICOM import DICOM
from Modules.MRI.Nifti_dump import Nifti_dump

types_list = {"MRI": (DICOM, Nifti_dump)}
ignoremodality = "__ignore__"
unknownmodality = "__unknown__"


def select(folder: str, module: str = ""):
    if module == "":
        for m in types_list:
            for cls in types_list[m]:
                if cls.isValidRecording(folder):
                    return cls
    else:
        for cls in types_list[module]:
            if cls.isValidRecording(folder):
                return cls
    return None


def select_file(file: str, module: str = ""):
    if module == "":
        for m in types_list:
            for cls in types_list[m]:
                if cls.isValidFile(file):
                    return cls
    else:
        for cls in types_list[module]:
            if cls.isValidFile(file):
                return cls
    return None

    for cls in types_list:
        return cls
    return None


def select_by_name(name: str, module: str = ""):
    if module == "":
        for m in types_list:
            for cls in types_list[m]:
                if cls.__name__ == name:
                    return cls
    else:
        for cls in types_list[module]:
            if cls.__name__ == name:
                return cls
    return None

    for cls in types_list:
        return cls
    return None
