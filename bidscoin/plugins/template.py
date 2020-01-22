# List of personalized, plugin-related errors
import tools.exceptions as Error

# Will integrate plugin into logging
import logging
logger = logging.getLogger(__name__)

# global variables
rawfolder = ""
bidsfolder = ""
dry_run = False


def InitEP(source: str, destination: str,
           dry: bool,
           **kwargs) -> int:
    """
    This code is run immideatly after loading plugin module
    It means to set-up global variables (like source folder)
    
    Global switch 'train' is defined to separate if plugin is 
    run by bidsmapper or bidscoiner. In train mode several
    tasks non-related to creating the map should be skipped.

    Global switch 'dry' is defined to allow to run in test mode, 
    where no actual file modification and writing should be 
    performed. Usefull to detect eventual errors.

    'kwargs' is there to allow plugin-specific options passed
    via CLI of CFI

    Parameters
    ----------
    source: str
        path to the source directory where 
        all original data files are stored
    destination: str
        path to the output folder, where all 
        sorted/bidsified files will be stored
    train: bool
        switch if it run for map creation (train=True)
        or for bidsification (train=False).
    dry: bool
        switch if it is a dry-run (True) where no modifiyng
        and/or creating of files occures, or nomal (False)
    kwargs:
        unspecified global parameters needed by plugin

    Returns
    -------
    int or None
        return code, if 0 (or None) Initialisation is 
        succesful. Non 0 if there some error, where
        code should indicate the problem. The code 
        must be in range [0-9]

    Raises
    ------
    Error.InitEPerror
        generic Initialisation error, code equivalent 100
    """
    global rawfolder
    global bidsfolder
    global train
    global dry_run
    rawfolder = source
    bidsfolder = destination
    map_creation = train
    dry_run = dry
    
    return 0

def SubjectEP(scan: dict) -> int:
    """
    This function is called after entering directory of subjects
    and meant to perform subject-global actions, like extracting 
    external data for given subject.

    The default (folder-defined) subject name can be modified 
    by modifying 'subject' field in the passed dictionary.
    The sub- prefix is optional for the modifyed subject 

    Parameters
    ----------
    scan: dict
        must contain fields 'subject' and 'session'

    Returns
    -------
    int or None
        return code, if 0 (or None) SubjectEP is 
        succesful. Non 0 if there some error, where
        code should indicate the problem. The code 
        must be in range [0-9]

    Raises
    ------
    Error.SubjectEPerror
        generic Initialisation error, code equivalent 110
    """
    return 0

def SessionEP(scan: dict) -> int:
    """
    This function is called after entering directory of session
    and meant to perform session-global actions, like parcing 
    session logs.

    The default (folder-defined) session name can be modified 
    by modifying 'session' field in the passed dictionary.
    The ses- prefix is optional for the modifyed subject 

    Parameters
    ----------
    scan: dict
        must contain fields 'subject' and 'session'

    Returns
    -------
    int or None
        return code, if 0 (or None) SessionEP is 
        succesful. Non 0 if there some error, where
        code should indicate the problem. The code 
        must be in range [0-9]

    Raises
    ------
    Error.SessionEPerror
        generic Initialisation error, code equivalent 120
    """
    return 0

def SequenceEP(recording: object) -> int:
    """
    This function is called after loading first file of
    a sequence and meant to perform sequence-global actions,
    like checking sequence order and validity.

    Custom recording-global variables can be defined here.

    Parameters
    ----------
    recording: Modules.base.baseModule
        A recording with loaded first file

    Returns
    -------
    int or None
        return code, if 0 (or None) SequenceEP is 
        succesful. Non 0 if there some error, where
        code should indicate the problem. The code 
        must be in range [0-9]

    Raises
    ------
    Error.SequenceEPerror
        generic Initialisation error, code equivalent 130
    """
    return 0

def RecordingEP(recording: object) -> int:
    """
    This function is called after loading each file of
    a sequence and meant to perform actions on recordings,
    like quality checks, and metafields corrections.
    
    Parameters
    ----------
    recording: Modules.base.baseModule
        A recording with loaded file

    Returns
    -------
    int or None
        return code, if 0 (or None) RecordingEP is 
        succesful. Non 0 if there some error, where
        code should indicate the problem. The code 
        must be in range [0-9]

    Raises
    ------
    Error.RecordingEPerror
        generic Initialisation error, code equivalent 140
    """
    return 0

def FileEP(recording: object) -> int:
    """
    This function is called after copiyng an individual
    recording file to its destination, for example checking
    its integrity.
    
    Parameters
    ----------
    recording: Modules.base.baseModule
        A recording with loaded file

    Returns
    -------
    int or None
        return code, if 0 (or None) RecordingEP is 
        succesful. Non 0 if there some error, where
        code should indicate the problem. The code 
        must be in range [0-9]

    Raises
    ------
    Error.FileEPerror
        generic Initialisation error, code equivalent 140
    """
    return 0

def SequenceEndEP(recording: object) -> int:
    """
    This function is called after treating all files from
    given sequence(recording). The currntFile for recording
    is the last file of sequence. It can be used to sequence
    global actions, like numkber of files check and combining.
    
    Parameters
    ----------
    recording: Modules.base.baseModule
        A recording with loaded file

    Returns
    -------
    int or None
        return code, if 0 (or None) RecordingEP is 
        succesful. Non 0 if there some error, where
        code should indicate the problem. The code 
        must be in range [0-9]

    Raises
    ------
    Error.SequenceEndEPerror
        generic Initialisation error, code equivalent 140
    """
    return 0

def FinaliseEP() -> int:
    """
    This function is called after treating all files from
    the source directory. All global final actions, like
    integrity checks can be performed there.
    
    Returns
    -------
    int or None
        return code, if 0 (or None) RecordingEP is 
        succesful. Non 0 if there some error, where
        code should indicate the problem. The code 
        must be in range [0-9]

    Raises
    ------
    Error.SequenceEndEPerror
        generic Initialisation error, code equivalent 140
    """
    return 0
