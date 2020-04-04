from . import MRI, EEG

types_list = {"MRI": (MRI.Nifti_SPM12, MRI.DICOM,),
              "EEG": (EEG.BrainVision,)}


def select(folder: str, module: str = ""):
    """
    Returns first class for wich given folder is correct

    Parameters
    ----------
    folder: str
        folder to scan
    module: str
        restrict type of class
    """
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


def selectFile(file: str, module: str = ""):
    """
    Returns first class for wich given file is correct

    Parameters
    ----------
    folder: str
        file to scan
    module: str
        restrict type of class
    """
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


def selectByName(name: str, module: str = ""):
    """
    Returns first class with given name

    Parameters
    ----------
    name: str
        name of class
    module: str
        restrict type of class
    """
    if module == "":
        for m in types_list:
            for cls in types_list[m]:
                if cls.Type() == name:
                    return cls
    else:
        for cls in types_list[module]:
            if cls.Type() == name:
                return cls
    return None
