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


def cleanup_value(label):
    """
    Converts a given label to a cleaned-up label
    that can be used as a BIDS label. 
    Remove leading and trailing spaces;
    convert other spaces, special BIDS characters and anything 
    that is not an alphanumeric to a ''. This will for example 
    map "Joe's reward_task" to "Joesrewardtask"

    :param label:   The given label
    :return:        The cleaned-up / BIDS-valid labe
    """

    if label is None:
        return label
    special_characters = (' ', '_', '-','.')
    for special in special_characters:
        label = str(label).strip().replace(special, '')

    return re.sub(r'(?u)[^-\w.]', '', label)

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
