import os
import re
import glob
import logging
import subprocess

logger = logging.getLogger(__name__)


def lsdirs(folder: str, wildcard: str='*'):
    """
    Gets all directories in a folder, ignores files

    :param folder:      The full pathname of the folder
    :param wildcard:    Simple (glob.glob) shell-style wildcards. 
                        Foldernames starting with a dot are special cases that 
                        are not matched by '*' and '?' patterns.") wildcard
    :return:            Iterable filter object with all directories in a folder
    """

    if wildcard:
        folder = os.path.join(folder, wildcard)
    return [fname for fname in sorted(glob.glob(folder))
            if os.path.isdir(fname)]


def cleanup_value(label, prefix=""):
    """
    Converts a given label to a cleaned-up label
    that can be used as a BIDS label. 
    Remove leading and trailing spaces;
    removes all non ASCII alphanumeric characters,
    for example "Joe's reward_task" changes to "Joesrewardtask"

    If prefix is specified, it will be added to final result.
    If prefix is present in initial field, it is removed, for ex:
    "task-Joe's reward_task" changes to "task-Joesrewardtask"
    if prefix is "task-"

    :param label:   The given label
    :param prefix:  Specified prefix
    :return:        The cleaned-up / BIDS-valid labe
    """

    if label is None:
        return label
    label = label.strip()
    if prefix and label.startswith(prefix):
        label = label[len(prefix):]
    if label == "":
        return label
    return prefix + re.sub(r'[^a-zA-Z0-9]', '', label, re.ASCII)


def match_value(val, regexp, force_str=False):
    if force_str:
        val = str(val).strip()
        regexp = regexp.strip()
        return re.fullmatch(regexp, val) is not None

    if isinstance(regexp, str):
        val = str(val).strip()
        regexp = regexp.strip()
        return re.fullmatch(regexp, val) is not None
    return val == regexp

def run_command(command: str) -> bool:
    """
    Runs a command in a shell using subprocess.run(command, ..)

    :param command: the command that is executed
    :return:        True if the were no errors, False otherwise
    """

    logger.info(f"Running: {command}")
    # TODO: investigate shell=False and capture_output=True for python 3.7
    process = subprocess.run(command, shell=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
    logger.info(f"Output:\n{process.stdout.decode('utf-8')}")

    if process.stderr.decode('utf-8') or process.returncode != 0:
        logger.error("Failed to run {} (errorcode {})"
                     .format(command, process.returncode))
        return False

    return True

def change_ext(filename, new_ext):
    pos = filename.rfind('.')
    if pos > 0 :
        filename = filename[:pos]
    return filename + "." + new_ext


def check_type(name: str, cls: type, val: object) -> object:
    """
    Checks if passed value is of type.

    Parameters:
    -----------
    name: str
        name of variable
    cls: type
        type to test
    val: object
        object to test

    Returns:
    --------
    object
        Succesfully tested object

    Raises:
    -------
    TypeError:
        if test is unsuccesful
    """
    if isinstance(val, cls):
        return val
    else:
        raise TypeError("{}: {} expected, {} recieved"
                        .format(name, cls, type(val)))
