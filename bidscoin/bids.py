#!/usr/bin/env python
"""
Module with helper functions

Some functions are derived from dac2bids.py from Daniel Gomez 29.08.2016
https://github.com/dangom/dac2bids/blob/master/dac2bids.py

@author: Marcel Zwiers
"""

# Global imports
import os.path
import copy
import glob
import inspect
import ast
import re
import logging
import coloredlogs
import subprocess
import pydicom
from importlib import util
from ruamel.yaml import YAML
yaml = YAML()

logger = logging.getLogger('bidscoin')

bidsmodalities  = ('fmap', 'anat', 'func', 'dwi', 'beh', 'pet')                                         # NB: get_matching_run() uses this order to search for a match
ignoremodality  = 'leave_out'
unknownmodality = 'extra_data'
bidslabels      = ('task', 'acq', 'ce', 'rec', 'dir', 'run', 'mod', 'echo', 'suffix', 'IntendedFor')    # This is not really something from BIDS, but these are the BIDS-labels used in the bidsmap


def bidsversion() -> str:
    """
    Reads the BIDS version from the BIDSVERSION.TXT file

    :return:    The BIDS version number
    """

    with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'bidsversion.txt')) as fid:
        version = fid.read().strip()

    return str(version)


def version() -> str:
    """
    Reads the BIDSCOIN version from the VERSION.TXT file

    :return:    The BIDSCOIN version number
    """

    with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'version.txt')) as fid:
        version = fid.read().strip()

    return str(version)


def setup_logging(log_file: str, debug: bool=False) -> logging.Logger:
    """
    Setup the logging

    :param log_file:    Name of the logfile
    :param debug:       Set log level to DEBUG if debug==True
    :return:            Logger object
     """

    # debug = True

    # Create the log dir if it does not exist
    logdir = os.path.dirname(log_file)
    os.makedirs(logdir, exist_ok=True)

    # Derive the name of the error logfile from the normal log_file
    error_file = os.path.splitext(log_file)[0] + '.errors'

    # Set the format and logging level
    fmt       = '%(asctime)s - %(name)s - %(levelname)s %(message)s'
    datefmt   = '%Y-%m-%d %H:%M:%S'
    formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)
    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    # Set & add the streamhandler and add some color to those boring terminal logs! :-)
    coloredlogs.install(level='DEBUG', fmt=fmt, datefmt=datefmt)

    # Set & add the log filehandler
    loghandler = logging.FileHandler(log_file)
    loghandler.setLevel(logging.DEBUG)
    loghandler.setFormatter(formatter)
    loghandler.set_name('loghandler')
    logger.addHandler(loghandler)

    # Set & add the error / warnings handler
    errorhandler = logging.FileHandler(error_file, mode='w')
    errorhandler.setLevel(logging.WARNING)
    errorhandler.setFormatter(formatter)
    errorhandler.set_name('errorhandler')
    logger.addHandler(errorhandler)

    return logger


def reporterrors():

    for filehandler in logger.handlers:
        if filehandler.name == 'errorhandler':

            errorfile = filehandler.baseFilename
            if os.path.getsize(errorfile):
                with open(errorfile, 'r') as fid:
                    errors = fid.read()
                logger.info(f"The following BIDScoin errors and warnings were reported:\n\n{40*'>'}\n{errors}{40*'<'}\n")

            else:
                logger.info(f'No BIDScoin errors or warnings were reported')
                logger.info('')

        elif filehandler.name == 'loghandler':
            logfile = filehandler.baseFilename

    logger.info(f'For the complete log see: {logfile}')
    logger.info(f'NB: logfiles may contain identifiable information, e.g. from pathnames')


def run_command(command: str) -> bool:
    """
    Runs a command in a shell using subprocess.run(command, ..)

    :param command: the command that is executed
    :return:        True if the were no errors, False otherwise
    """

    logger.info(f"Running: {command}")
    process = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)          # TODO: investigate shell=False and capture_output=True for python 3.7
    logger.info(f"Output:\n{process.stdout.decode('utf-8')}")

    if process.stderr.decode('utf-8') or process.returncode!=0:
        logger.error(f"Failed to run {command} (errorcode {process.returncode})")
        return False

    return True


def import_plugin(plugin: str):
    """

    :param plugin:  Name of the plugin
    :return:        plugin-module
    """

    # Get the full path to the plugin-module
    if os.path.basename(plugin)==plugin:
        plugin = os.path.join(os.path.dirname(__file__), 'plugins', plugin)
    else:
        plugin = plugin
    plugin = os.path.abspath(os.path.expanduser(plugin))

    # See if we can find the plug-in
    if not os.path.isfile(plugin):
        logger.error(f"Could not find plugin: '{plugin}'")
        return None

    # Load the plugin-module
    try:
        spec   = util.spec_from_file_location('bidscoin_plugin', plugin)
        module = util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # bidsmapper -> module.bidsmapper_plugin(runfolder, bidsmap_new, bidsmap_old)
        if 'bidsmapper_plugin' not in dir(module):
            logger.info('Could not find bidscoiner_plugin() in ' + plugin)

        # bidscoiner -> module.bidscoiner_plugin(session, bidsmap, bidsfolder, personals)
        if 'bidscoiner_plugin' not in dir(module):
            logger.info('Could not find bidscoiner_plugin() in ' + plugin)

        if 'bidsmapper_plugin' not in dir(module) and 'bidscoiner_plugin' not in dir(module):
            logger.warning(f"{plugin} can (and will) not perform any operation")

        return module

    except Exception:
        logger.exception(f"Could not import '{plugin}'")

        return None


def test_tooloptions(tool: str, opts: dict) -> bool:
    """
    Performs tests of the user tool parameters set in bidsmap['Options']

    :param tool:    Name of the tool that is being tested in bidsmap['Options']
    :param opts:    The editable options belonging to the tool
    :return:        True if the tool generated the expected result, False if there was a tool error
    """

    if tool == 'dcm2niix':
        command = f"{opts['path']}dcm2niix -h"
    elif tool == 'bidscoin':
        command = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'bidscoin.py -v')
    else:
        logger.warning(f"Testing of '{tool}' not supported")
        return None

    logger.info(f"Testing: '{tool}'")

    return run_command(command)


def test_plugins(plugin: str='') -> bool:
    """
    Performs tests of the plug-ins in bidsmap['PlugIns']

    :param plugin:  The name of the plugin that is being tested (-> bidsmap['Plugins'])
    :return:        True if the plugin generated the expected result, False if there
                    was a plug-in error, None if this function has an implementation error
    """

    logger.info(f"Testing: '{plugin}' plugin")

    module = import_plugin(plugin)
    if inspect.ismodule(module):
        methods = [method for method in dir(module) if not method.startswith('_')]
        logger.info(f"Result:\n{module.__doc__}\n{plugin} attributes and methods:\n{methods}\n")
        return True

    else:
        return False


def lsdirs(folder: str, wildcard: str='*'):
    """
    Gets all directories in a folder, ignores files

    :param folder:      The full pathname of the folder
    :param wildcard:    Simple (glob.glob) shell-style wildcards. Foldernames starting with a dot are special cases that are not matched by '*' and '?' patterns.") wildcard
    :return:            An iterable filter object with all directories in a folder
    """

    if wildcard:
        folder = os.path.join(folder, wildcard)
    return [fname for fname in sorted(glob.glob(folder)) if os.path.isdir(fname)]


def is_dicomfile(file: str) -> bool:
    """
    Checks whether a file is a DICOM-file. It uses the feature that Dicoms have the string DICM hardcoded at offset 0x80.

    :param file:    The full pathname of the file
    :return:        Returns true if a file is a DICOM-file
    """

    if os.path.isfile(file):
        if os.path.basename(file).startswith('.'):
            logger.warning(f'DICOM file is hidden: {file}')
        with open(file, 'rb') as dcmfile:
            dcmfile.seek(0x80, 1)
            if dcmfile.read(4) == b'DICM':
                return True
            else:
                dicomdict = pydicom.dcmread(file, force=True)       # The DICM tag may be missing for anonymized DICOM files
                return 'Modality' in dicomdict
    else:
        return False


def is_dicomfile_siemens(file: str) -> bool:
    """
    Checks whether a file is a *SIEMENS* DICOM-file. All Siemens Dicoms contain a dump of the
    MrProt structure. The dump is marked with a header starting with 'ASCCONV BEGIN'. Though
    this check is not foolproof, it is very unlikely to fail.

    :param file:    The full pathname of the file
    :return:        Returns true if a file is a Siemens DICOM-file
    """

    return b'ASCCONV BEGIN' in open(file, 'rb').read()


def is_parfile(file: str) -> bool:
    """
    Checks whether a file is a Philips PAR file

    WIP!!!!!!

    :param file:    The full pathname of the file
    :return:        Returns true if a file is a Philips PAR-file
    """

    # TODO: Returns true if filetype is PAR.
    if os.path.isfile(file):
        with open(file, 'r') as parfile:
            pass
        return False


def is_p7file(file: str) -> bool:
    """
    Checks whether a file is a GE P*.7 file

    WIP!!!!!!

    :param file:    The full pathname of the file
    :return:        Returns true if a file is a GE P7-file
    """

    # TODO: Returns true if filetype is P7.
    if os.path.isfile(file):
        with open(file, 'r') as p7file:
            pass
        return False


def is_niftifile(file: str) -> bool:
    """
    Checks whether a file is a nifti file

    WIP!!!!!!

    :param file:    The full pathname of the file
    :return:        Returns true if a file is a nifti-file
    """

    # TODO: Returns true if filetype is nifti.
    if os.path.isfile(file):
        with open(file, 'r') as niftifile:
            pass
        return False


def is_incomplete_acquisition(folder: str) -> bool:
    """
    If a scan was aborted in the middle of the experiment, it is likely that images will be saved
    anyway. We want to avoid converting these incomplete directories. This function checks the number
    of measurements specified in the protocol against the number of imaging files in the folder.

    :param folder:  The full pathname of the folder
    :return:        Returns true if the acquisition was incomplete
    """

    dicomfile = get_dicomfile(folder)
    nrep      = get_dicomfield('lRepetitions', dicomfile)
    nfiles    = len(os.listdir(folder))     # TODO: filter out non-imaging files

    if nrep and nrep > nfiles:
        logger.warning('Incomplete acquisition found in: {}'\
                       '\nExpected {}, found {} dicomfiles'.format(folder, nrep, nfiles))
        return True
    else:
        return False


def get_dicomfile(folder: str) -> str:
    """
    Gets a dicom-file from the folder

    :param folder:  The full pathname of the folder
    :return:        The filename of the first dicom-file in the folder.
    """

    for file in sorted(os.listdir(folder)):
        if os.path.basename(file).startswith('.'):
            logger.warning(f'Ignoring hidden DICOM file: {file}')
            continue
        if is_dicomfile(os.path.join(folder, file)):
            return os.path.join(folder, file)

    logger.warning('Cannot find dicom files in:' + folder)
    return None


def get_parfile(folder: str) -> str:
    """
    Gets a Philips PAR-file from the folder

    :param folder:  The full pathname of the folder
    :return:        The filename of the first PAR-file in the folder.
    """

    for file in sorted(os.listdir(folder)):
        if is_parfile(file):
            return os.path.join(folder, file)

    logger.warning('Cannot find PAR files in:' + folder)
    return None


def get_p7file(folder: str) -> str:
    """
    Gets a GE P*.7-file from the folder

    :param folder:  The full pathname of the folder
    :return:        The filename of the first P7-file in the folder.
    """

    for file in sorted(os.listdir(folder)):
        if is_p7file(file):
            return os.path.join(folder, file)

    logger.warning('Cannot find P7 files in:' + folder)
    return None


def get_niftifile(folder: str) -> str:
    """
    Gets a nifti-file from the folder

    :param folder:  The full pathname of the folder
    :return:        The filename of the first nifti-file in the folder.
    """

    for file in sorted(os.listdir(folder)):
        if is_niftifile(file):
            return os.path.join(folder, file)

    logger.warning('Cannot find nifti files in:' + folder)
    return None


def load_bidsmap(yamlfile: str='', folder: str='', report: bool=True) -> (dict, str):
    """
    Read the mapping heuristics from the bidsmap yaml-file. If yamlfile is not fullpath, then 'folder' is first searched before
    the default 'heuristics'. If yamfile is empty, then first 'bidsmap.yaml' is searched for, them 'bidsmap_template.yaml'. So fullpath
    has precendence over folder and bidsmap.yaml has precedence over bidsmap_template.yaml

    :param yamlfile:    The full pathname or basename of the bidsmap yaml-file. If None, the default bidsmap_template.yaml file in the heuristics folder is used
    :param folder:      Only used when yamlfile=basename or None: yamlfile is then first searched for in folder and then falls back to the ./heuristics folder (useful for centrally managed template yaml-files)
    :param report:      Report log.info when reading a file
    :return:            Tuple with (1) ruamel.yaml dict structure, with all options, BIDS mapping heuristics, labels and attributes, etc and (2) the fullpath yaml-file
    """

    # Input checking
    heuristics_folder = os.path.join(os.path.dirname(__file__),'..','heuristics')
    if not folder:
        folder = heuristics_folder
    if not yamlfile:
        yamlfile = os.path.join(folder,'bidsmap.yaml')
        if not os.path.isfile(yamlfile):
            yamlfile = os.path.join(heuristics_folder,'bidsmap_template.yaml')

    # Add a standard file-extension if needed
    if not os.path.splitext(yamlfile)[1]:
        yamlfile = yamlfile + '.yaml'

    # Get the full path to the bidsmap yaml-file
    if os.path.basename(yamlfile) == yamlfile:
        if os.path.isfile(os.path.join(folder, yamlfile)):
            yamlfile = os.path.join(folder, yamlfile)
        else:
            yamlfile = os.path.join(heuristics_folder, yamlfile)

    yamlfile = os.path.abspath(os.path.expanduser(yamlfile))
    if not os.path.isfile(yamlfile):
        logger.info('No bidsmap file found: ' + os.path.abspath(yamlfile))
        return dict(), yamlfile
    elif report:
        logger.info('Reading: ' + os.path.abspath(yamlfile))

    # Read the heuristics from the bidsmap file
    with open(yamlfile, 'r') as stream:
        bidsmap = yaml.load(stream)

    # Issue a warning if the version in the bidsmap YAML-file is not the same as the bidscoin version
    if 'bidscoin' in bidsmap['Options'] and 'version' in bidsmap['Options']['bidscoin']:
        bidsmapversion = bidsmap['Options']['bidscoin']['version']
    elif 'version' in bidsmap['Options']:
        bidsmapversion = bidsmap['Options']['version']
    else:
        bidsmapversion = 'Unknown'

    if bidsmapversion != version():
        logger.warning(f'BIDScoiner version conflict: {yamlfile} was created using version {bidsmapversion}, but this is version {version()}')

    # Make sure we get a proper list of plugins
    if not bidsmap['PlugIns']:
        bidsmap['PlugIns'] = []
    bidsmap['PlugIns'] = [plugin for plugin in bidsmap['PlugIns'] if plugin]

    return bidsmap, yamlfile


def save_bidsmap(filename: str, bidsmap: dict):
    """
    Save the BIDSmap as a YAML text file

    :param filename:
    :param bidsmap:         Full bidsmap data structure, with all options, BIDS labels and attributes, etc
    :return:
    """

    logger.info('Writing bidsmap to: ' + filename)
    with open(filename, 'w') as stream:
        yaml.dump(bidsmap, stream)

    # See if we can reload it, i.e. whether it is valid yaml...
    try:
        load_bidsmap(filename, '', False)
    except:
        logger.error(f'The saved output bidsmap does not seem to be valid YAML, please check {filename}, e.g. by way of an online yaml validator, such as https://yamlchecker.com/')


def parse_x_protocol(pattern: str, dicomfile: str) -> str:
    """
    Siemens writes a protocol structure as text into each DICOM file.
    This structure is necessary to recreate a scanning protocol from a DICOM,
    since the DICOM information alone wouldn't be sufficient.

    :param pattern:     A regexp expression: '^' + pattern + '\t = \t(.*)\\n'
    :param dicomfile:   The full pathname of the dicom-file
    :return:            The string extracted values from the dicom-file according to the given pattern
    """

    if not is_dicomfile_siemens(dicomfile):
        logger.warning('Parsing {} may fail because {} does not seem to be a Siemens DICOM file'.format(pattern, dicomfile))

    regexp = '^' + pattern + '\t = \t(.*)\n'
    regex  = re.compile(regexp.encode('utf-8'))

    with open(dicomfile, 'rb') as openfile:
        for line in openfile:
            match = regex.match(line)
            if match:
                return match.group(1).decode('utf-8')

    logger.warning('Pattern: "' + regexp.encode('unicode_escape').decode() + '" not found in: ' + dicomfile)
    return None


# Profiling shows this is currently the most expensive function, so therefore the (primitive but effective) _DICOMDICT_CACHE optimization
_DICOMDICT_CACHE = None
_DICOMFILE_CACHE = None
def get_dicomfield(tagname: str, dicomfile: str):
    """
    Robustly extracts a DICOM field/tag from a dictionary or from vendor specific fields

    :param tagname:     Name of the DICOM field
    :param dicomfile:   The full pathname of the dicom-file
    :return:            Extracted tag-values from the dicom-file
    """

    global _DICOMDICT_CACHE, _DICOMFILE_CACHE

    if not os.path.isfile(dicomfile):
        logger.warning(f"{dicomfile} not found")
        value = None

    else:
        try:
            if dicomfile != _DICOMFILE_CACHE:
                dicomdict = pydicom.dcmread(dicomfile, force=True)      # The DICM tag may be missing for anonymized DICOM files
                if 'Modality' not in dicomdict:
                    raise ValueError(f'Cannot read {dicomfile}')
                _DICOMDICT_CACHE = dicomdict
                _DICOMFILE_CACHE = dicomfile
            else:
                dicomdict = _DICOMDICT_CACHE

            value = dicomdict.get(tagname)

            # Try a recursive search
            if not value:
                for elem in dicomdict.iterall():
                    if elem.name==tagname:
                        value = elem.value
                        continue

        except IOError:
            logger.warning(f'Cannot read {tagname} from {dicomfile}')
            value = None

        except Exception:
            try:
                value = parse_x_protocol(tagname, dicomfile)

            except Exception:
                logger.warning(f'Could not parse {tagname} from {dicomfile}')
                value = None

    # Cast the dicom datatype to int or str (i.e. to something that yaml.dump can handle)
    if not value:
        return ''

    elif isinstance(value, int):
        return int(value)

    elif not isinstance(value, str):    # Assume it's a MultiValue type and flatten it
        return str(value)

    else:
        return str(value)


def add_prefix(prefix: str, tag: str) -> str:
    """
    Simple function to account for optional BIDS tags in the bids file names, i.e. it prefixes 'prefix' only when tag is not empty

    :param prefix:  The prefix (e.g. '_sub-')
    :param tag:     The tag (e.g. 'control01')
    :return:        The tag with the leading prefix (e.g. '_sub-control01') or just the empty tag ''
    """

    if tag:
        tag = prefix + str(tag)
    else:
        tag = ''

    return tag


def strip_suffix(run: dict) -> dict:
    """
    Certain attributes such as SeriesDescriptions (but not ProtocolName!?) may get a suffix like '_SBRef' from the vendor,
    try to strip it off from the BIDS labels

    :param run: The run with potentially added suffixes that are the same as the BIDS suffixes
    :return:    The run with these suffixes removed
    """

    # See if we have a suffix for this modality
    if 'suffix' in run['bids'] and run['bids']['suffix']:
        suffix = run['bids']['suffix'].lower()
    else:
        return run

    # See if any of the BIDS labels ends with the same suffix. If so, then remove it
    for key in run['bids']:
        if key == 'suffix':
            continue
        if isinstance(run['bids'][key], str) and run['bids'][key].lower().endswith(suffix):
            run['bids'][key] = run['bids'][key][0:-len(suffix)]       # NB: This will leave the added '_' and '.' characters, but they will be taken out later (as they are not BIDS-valid)

    return run


def cleanup_value(label):
    """
    Converts a given label to a cleaned-up label that can be used as a BIDS label. Remove leading and trailing spaces;
    convert other spaces, special BIDS characters and anything that is not an alphanumeric to a ''. This will for
    example map "Joe's reward_task" to "Joesrewardtask"

    :param label:   The given label that potentially contains undesired characters
    :return:        The cleaned-up / BIDS-valid label
    """

    if label is None:
        return label

    special_characters = (' ', '_', '-','.')

    for special in special_characters:
        label = str(label).strip().replace(special, '')

    return re.sub(r'(?u)[^-\w.]', '', label)


def dir_bidsmap(bidsmap: dict, source: str) -> list:
    """
    Make a provenance list of all the runs in the bidsmap[source]

    :param bidsmap: The bidsmap, with all the runs in it
    :param source:  The information source in the bidsmap that is used, e.g. 'DICOM'
    :return:        List of all provenances
    """

    provenance = []
    for modality in bidsmodalities + (unknownmodality, ignoremodality):
        if modality in bidsmap[source] and bidsmap[source][modality]:
            for run in bidsmap[source][modality]:
                provenance.append(run['provenance'])
                if not run['provenance']:
                    logger.warning(f'The bidsmap run {modality} run does not contain provenance data')

    provenance.sort()

    return provenance


def get_run(bidsmap: dict, source: str, modality, suffix_idx, dicomfile: str='') -> dict:
    """
    Find the (first) run in bidsmap[source][bidsmodality] with run['bids']['suffix_idx'] == suffix_idx

    :param bidsmap:     This could be a template bidsmap, with all options, BIDS labels and attributes, etc
    :param source:      The information source in the bidsmap that is used, e.g. 'DICOM'
    :param modality:    The modality in which a matching run is searched for (e.g. 'anat')
    :param suffix_idx:  The name of the suffix that is searched for (e.g. 'bold') or the modality index number
    :param dicomfile:   The name of the dicomfile. If given, the DICOM values are read from file
    :return:            The clean (filled) run item in the bidsmap[source][bidsmodality] with the matching suffix_idx, otherwise None
    """

    for index, run in enumerate(bidsmap[source][modality]):
        if index == suffix_idx or run['bids']['suffix'] == suffix_idx:

            run_ = dict(provenance={}, attributes={}, bids={})

            for attrkey, attrvalue in run['attributes'].items():
                if dicomfile:
                    run_['attributes'][attrkey] = get_dicomfield(attrkey, dicomfile)
                    run_['provenance']          = dicomfile
                else:
                    run_['attributes'][attrkey] = attrvalue

            for bidskey, bidsvalue in run['bids'].items():
                if dicomfile:
                    run_['bids'][bidskey] = get_dynamic_value(bidsvalue, dicomfile)
                else:
                    run_['bids'][bidskey] = bidsvalue

            return run_

    logger.error(f"'{modality}' run with suffix_idx '{suffix_idx}' not found in bidsmap['{source}']")


def delete_run(bidsmap: dict, source: str, modality: str, provenance: str) -> dict:
    """
    Delete a run from the BIDS map

    :param bidsmap:     Full bidsmap data structure, with all options, BIDS labels and attributes, etc
    :param source:      The information source in the bidsmap that is used, e.g. 'DICOM'
    :param modality:    The modality in the source that is used, e.g. 'anat'
    :param provenance:  The unique provance that is use to identify the run
    :return:            The new bidsmap
    """

    for index, run in enumerate(bidsmap[source][modality]):
        if run['provenance'] == provenance:
            del bidsmap[source][modality][index]

    return bidsmap


def append_run(bidsmap: dict, source: str, modality: str, run: dict, clean: bool=True) -> dict:
    """
    Append a run to the BIDS map

    :param bidsmap:     Full bidsmap data structure, with all options, BIDS labels and attributes, etc
    :param source:      The information source in the bidsmap that is used, e.g. 'DICOM'
    :param modality:    The modality in the source that is used, e.g. 'anat'
    :param run:         The run (listitem) that is appenden to the modality
    :return:            The new bidsmap
    """

    # Copy the values from the run to an empty dict
    if clean:
        run_ = dict(provenance={}, attributes={}, bids={})

        run_['provenance'] = run['provenance']

        for key, value in run['attributes'].items():
            run_['attributes'][key] = value
        for key, value in run['bids'].items():
            run_['bids'][key] = value

        run = run_

    if bidsmap[source][modality] is None:
        bidsmap[source][modality] = [run]
    else:
        bidsmap[source][modality].append(run)

    return bidsmap


def update_bidsmap(bidsmap: dict, source_modality: str, provenance: str, target_modality: str, run: dict, source: str= 'DICOM', clean: bool=True) -> dict:
    """
    Update the BIDS map if the modality changes:
    1. Remove the source run from the source modality section
    2. Append the (cleaned) target run to the target modality section

    Else:
    1. Use the provenance to look-up the index number in that modality
    2. Replace the run

    :param bidsmap:             Full bidsmap data structure, with all options, BIDS labels and attributes, etc
    :param source_modality:     The current modality name, e.g. 'anat'
    :param provenance:          The unique provance that is use to identify the run
    :param target_modality:     The modality name what is should be, e.g. 'dwi'
    :param run:                 The run item that is being moved
    :param source:              The name of the information source, e.g. 'DICOM'
    :param clean:               A boolean that is passed to bids.append_run (telling it to clean-up commentedMap fields)
    :return:
    """

    num_runs_in = len(dir_bidsmap(bidsmap, source))

    # Warn the user if the target run already exists when the run is moved to another modality
    if source_modality!=target_modality:
        if exist_run(bidsmap, source, target_modality, run):
            logger.warning(f'That run from {source_modality} already exists in {target_modality}...')

        # Delete the source run
        bidsmap = delete_run(bidsmap, source, source_modality, provenance)

        # Append the (cleaned-up) target run
        bidsmap = append_run(bidsmap, source, target_modality, run, clean)

    else:
        for index, run_ in enumerate(bidsmap[source][target_modality]):
            if run_['provenance'] == provenance:
                bidsmap[source][target_modality][index] = run
                break

    num_runs_out = len(dir_bidsmap(bidsmap, source))
    if num_runs_out != num_runs_in:
        logger.error(f"Number of runs in bidsmap['{source}'] changed unexpectedly: {num_runs_in} -> {num_runs_out}")

    return bidsmap


def match_attribute(longvalue, values) -> bool:
    """
    Compare the value items with / without *wildcard* with the longvalue string. If both longvalue
    and values are a list then they are directly compared as is

    Examples:
        match_attribute('my_pulse_sequence_name', 'name') -> False
        match_attribute('my_pulse_sequence_name', '*name*') -> True
        match_attribute('T1_MPRAGE', '['T1w', 'MPRAGE']') -> False
        match_attribute('T1_MPRAGE', '['T1w', 'T1_MPRAGE']') -> True
        match_attribute('T1_MPRAGE', '['*T1w*', '*MPRAGE*']') -> True

    :param longvalue:   The long string that is being searched in
    :param values:      Either a list with search items or a string that is matched one-to-one
    :return:            True if a match is found or both longvalue and values are identical or
                        empty / None. False otherwise
    """

    # Consider it a match if both longvalue and values are identical or empty / None
    if longvalue==values or (not longvalue and not values):
        return True

    if not longvalue or not values:
        return False

    # Make sure we start with string types
    longvalue = str(longvalue)
    values    = str(values)

    # Interpret attribute lists as lists
    def cast2list(string: str):
        if string.startswith('[') and string.endswith(']'):
            try:
                string = ast.literal_eval(string)
                if not isinstance(string, list):
                    logger.error(f"Attribute value '{string}' is not a list")
            except:
                logger.error(f"Could not interpret attribute value '{string}'")
        return string

    longvalue = cast2list(longvalue)
    values    = cast2list(values)

    # Account for lists in the template (to combine similar mappings)
    if not isinstance(values, list):
        values = [values]

    # If they are both lists, compare them as they are
    elif isinstance(longvalue, list):
        return str(longvalue)==str(values)

    # Compare the value items (with / without wildcard) with the longvalue string
    for value in values:

        value = str(value)

        if value in ('*', '**'):
            return True

        if value.startswith('*') and value.endswith('*') and value[1:-1] in longvalue:
            return True

        elif value==longvalue:
            return True

    return False


def exist_run(bidsmap: dict, source: str, modality: str, run_item: dict, matchbidslabels: bool=False) -> bool:
    """
    Checks if there is already an entry in runlist with the same attributes and, optionally, bids values as in the input run

    :param bidsmap:         Full bidsmap data structure, with all options, BIDS labels and attributes, etc
    :param source:          The information source in the bidsmap that is used, e.g. 'DICOM'
    :param modality:        The modality in the source that is used, e.g. 'anat'. Empty values will search through all modalities
    :param run_item:        The run (listitem) that is searched for in the modality
    :param matchbidslabels: If True, also matches the BIDS-labels, otherwise only run['attributes']
    :return:                True if the run exists in runlist
    """

    if not modality:
        for modality in bidsmodalities + (unknownmodality, ignoremodality):
            if exist_run(bidsmap, source, modality, run_item, matchbidslabels):
                return True

    if not bidsmap[source] or not bidsmap[source][modality]:
        return False

    for run in bidsmap[source][modality]:

        # Begin with match = False only if all attributes are empty
        match = any([run_item['attributes'][key] is not None for key in run_item['attributes']])

        # Search for a case where all run_item items match with the run_item items
        for itemkey, itemvalue in run_item['attributes'].items():
            value = run['attributes'].get(itemkey, None)    # Matching bids-labels which exist in one modality but not in the other -> None
            match = match and match_attribute(itemvalue, value)
            if not match:
                break                                       # There is no point in searching further within the run_item now that we've found a mismatch

        # See if the bidslabels also all match. This is probably not very useful, but maybe one day...
        if matchbidslabels and match:
            for itemkey, itemvalue in run_item['bids'].items():
                value = run['bids'].get(itemkey, None)      # Matching bids-labels which exist in one modality but not in the other -> None
                match = match and value==itemvalue
                if not match:
                    break                                   # There is no point in searching further within the run_item now that we've found a mismatch

        # Stop searching if we found a matching run_item (i.e. which is the case if match is still True after all run tests). TODO: maybe count how many instances, could perhaps be useful info
        if match:
            return True

    return False


def get_matching_run(dicomfile: str, bidsmap: dict, modalities: tuple = bidsmodalities + (ignoremodality, unknownmodality)) -> tuple:
    """
    Find the first run in the bidsmap with dicom attributes that match with the dicom file. Then update the (dynamic) bids values (values are cleaned-up to be BIDS-valid)

    :param dicomfile:   The full pathname of the dicom-file
    :param bidsmap:     Full bidsmap data structure, with all options, BIDS labels and attributes, etc
    :param modalities:  The modality in which a matching run is searched for. Default = bidsmodalities + (ignoremodality, unknownmodality)
    :return:            (run, modality, index) The matching and filled-in / cleaned run item, modality and list index as in run = bidsmap[DICOM][modality][index]
                        modality = bids.unknownmodality and index = None if there is no match, the run is still populated with info from the dicom-file
    """

    source = 'DICOM'                                                                                        # TODO: generalize for non-DICOM (dicomfile -> file)?
    run_   = dict(provenance={}, attributes={}, bids={})

    # Loop through all bidsmodalities and runs; all info goes into run_
    for modality in modalities:
        if bidsmap[source][modality] is None: continue

        for index, run in enumerate(bidsmap[source][modality]):

            run_  = dict(provenance={}, attributes={}, bids={})                                             # The CommentedMap API is not guaranteed for the future so keep this line as an alternative
            match = any([run['attributes'][attrkey] is not None for attrkey in run['attributes']])          # Normally match==True, but make match==False if all attributes are empty

            # Try to see if the dicomfile matches all of the attributes and fill all of them
            for attrkey, attrvalue in run['attributes'].items():

                # Check if the attribute value matches with the info from the dicomfile
                dicomvalue = get_dicomfield(attrkey, dicomfile)
                if attrvalue:
                    match = match and match_attribute(dicomvalue, attrvalue)

                # Fill the empty attribute with the info from the dicomfile
                run_['attributes'][attrkey] = dicomvalue

            # Try to fill the bids-labels
            for bidskey, bidsvalue in run['bids'].items():

                # Replace the dynamic bids values
                run_['bids'][bidskey] = get_dynamic_value(bidsvalue, dicomfile)

                # SeriesDescriptions (and ProtocolName?) may get a suffix like '_SBRef' from the vendor, try to strip it off
                run_ = strip_suffix(run_)

            # Stop searching the bidsmap if we have a match. TODO: check if there are more matches (i.e. conflicts)
            if match:
                run_['provenance'] = dicomfile

                return run_, modality, index

    # We don't have a match (all tests failed, so modality should be the *last* one, i.e. unknownmodality)
    logger.debug(f"Could not find a matching run in the bidsmap for {dicomfile} -> {modality}")
    run_['provenance'] = dicomfile

    return run_, modality, None


def get_subid_sesid(dicomfile: str, subid: str='', sesid: str='', subprefix: str= 'sub-', sesprefix: str= 'ses-'):
    """
    Extract the cleaned-up subid and sesid from the pathname or from the dicom file if subid/sesid == '<<SourceFilePath>>'

    :param dicomfile:   The full pathname of the dicomfile. If given, the DICOM values are read from the file
    :param subid:       The subject identifier, i.e. name of the subject folder (e.g. 'sub-001' or just '001'). Can be left empty
    :param sesid:       The optional session identifier, i.e. name of the session folder (e.g. 'ses-01' or just '01'). Can be left empty
    :param subprefix:   The optional subprefix (e.g. 'sub-'). Used to parse the sub-value from the provenance as default subid
    :param sesprefix:   The optional sesprefix (e.g. 'ses-'). If it is found in the provenance then a default sesid will be set
    :return:            Updated (subid, sesid) tuple, including the sub/sesprefix
    """

    # Add default value for subid and sesid (e.g. for the bidseditor)
    dicompath = os.path.dirname(dicomfile)
    if not subid or subid=='<<SourceFilePath>>':
        subid = dicompath.rsplit(os.sep + subprefix, 1)[1].split(os.sep)[0]
    else:
        subid = get_dynamic_value(subid, dicomfile)
    if not sesid or sesid=='<<SourceFilePath>>':
        if os.sep + sesprefix in dicompath:
            sesid = dicompath.rsplit(os.sep + sesprefix, 1)[1].split(os.sep)[0]
        else:
            sesid = ''
    else:
        sesid = get_dynamic_value(sesid, dicomfile)

    # Add sub- and ses- prefixes if they are not there
    subid = 'sub-' + cleanup_value(re.sub(f'^{subprefix}', '', subid))
    if sesid:
        sesid = 'ses-' + cleanup_value(re.sub(f'^{sesprefix}', '', sesid))

    return subid, sesid


def get_bidsname(subid: str, sesid: str, modality: str, run: dict, runindex: str= '', subprefix: str= 'sub-', sesprefix: str= 'ses-') -> str:
    """
    Composes a filename as it should be according to the BIDS standard using the BIDS labels in run

    :param subid:       The subject identifier, i.e. name of the subject folder (e.g. 'sub-001' or just '001'). Can be left empty
    :param sesid:       The optional session identifier, i.e. name of the session folder (e.g. 'ses-01' or just '01'). Can be left empty
    :param modality:    The bidsmodality (choose from bids.bidsmodalities)
    :param run:         The run mapping with the BIDS labels
    :param runindex:    The optional runindex label (e.g. 'run-01'). Can be left ''
    :param subprefix:   The optional subprefix (e.g. 'sub-'). Used to parse the sub-value from the provenance as default subid
    :param sesprefix:   The optional sesprefix (e.g. 'ses-'). If it is found in the provenance then a default sesid will be set
    :return:            The composed BIDS file-name (without file-extension)
    """
    assert modality in bidsmodalities + (unknownmodality, ignoremodality)

    # Try to update the sub/ses-ids
    subid, sesid = get_subid_sesid(run['provenance'], subid, sesid, subprefix, sesprefix)

    # Validate and do some checks to allow for dragging the run entries between the different modality-sections
    run = copy.deepcopy(run)                # Avoid side effects when changing run
    for bidslabel in bidslabels:
        if bidslabel not in run['bids']:
            run['bids'][bidslabel] = None
        else:
            run['bids'][bidslabel] = cleanup_value(get_dynamic_value(run['bids'][bidslabel], run['provenance']))

    # Use the clean-up runindex
    if not runindex:
        runindex = run['bids']['run']

    # Compose the BIDS filename (-> switch statement)
    if modality == 'anat':

        # bidsname: sub-<participant_label>[_ses-<session_label>][_acq-<label>][_ce-<label>][_rec-<label>][_run-<index>][_mod-<label>]_suffix
        bidsname = '{sub}{_ses}{_acq}{_ce}{_rec}{_run}{_mod}_{suffix}'.format(
            sub     = subid,
            _ses    = add_prefix('_', sesid),
            _acq    = add_prefix('_acq-', run['bids']['acq']),
            _ce     = add_prefix('_ce-',  run['bids']['ce']),
            _rec    = add_prefix('_rec-', run['bids']['rec']),
            _run    = add_prefix('_run-', runindex),
            _mod    = add_prefix('_mod-', run['bids']['mod']),
            suffix  = run['bids']['suffix'])

    elif modality == 'func':

        # bidsname: sub-<label>[_ses-<label>]_task-<label>[_acq-<label>][_ce-<label>][_dir-<label>][_rec-<label>][_run-<index>][_echo-<index>]_<contrast_label>.nii[.gz]
        bidsname = '{sub}{_ses}_{task}{_acq}{_ce}{_dir}{_rec}{_run}{_echo}_{suffix}'.format(
            sub     = subid,
            _ses    = add_prefix('_', sesid),
            task    = f"task-{run['bids']['task']}",
            _acq    = add_prefix('_acq-',  run['bids']['acq']),
            _ce     = add_prefix('_ce-',   run['bids']['ce']),
            _dir    = add_prefix('_dir-',  run['bids']['dir']),
            _rec    = add_prefix('_rec-',  run['bids']['rec']),
            _run    = add_prefix('_run-',  runindex),
            _echo   = add_prefix('_echo-', run['bids']['echo']),
            suffix  = run['bids']['suffix'])

    elif modality == 'dwi':

        # bidsname: sub-<label>[_ses-<label>][_acq-<label>][_dir-<label>][_run-<index>]_dwi.nii[.gz]
        bidsname = '{sub}{_ses}{_acq}{_dir}{_run}_{suffix}'.format(
            sub     = subid,
            _ses    = add_prefix('_', sesid),
            _acq    = add_prefix('_acq-', run['bids']['acq']),
            _dir    = add_prefix('_dir-', run['bids']['dir']),
            _run    = add_prefix('_run-', runindex),
            suffix  = run['bids']['suffix'])

    elif modality == 'fmap':

        # TODO: add more fieldmap logic?

        # bidsname: sub-<label>[_ses-<label>][_acq-<label>][_ce-<label>]_dir-<label>[_run-<index>]_epi.nii[.gz]
        bidsname = '{sub}{_ses}{_acq}{_ce}{_dir}{_run}_{suffix}'.format(
            sub     = subid,
            _ses    = add_prefix('_', sesid),
            _acq    = add_prefix('_acq-', run['bids']['acq']),
            _ce     = add_prefix('_ce-',  run['bids']['ce']),
            _dir    = add_prefix('_dir-', run['bids']['dir']),
            _run    = add_prefix('_run-', runindex),
            suffix  = run['bids']['suffix'])

    elif modality == 'beh':

        # bidsname: sub-<participant_label>[_ses-<session_label>]_task-<task_name>_suffix
        bidsname = '{sub}{_ses}_{task}_{suffix}'.format(
            sub     = subid,
            _ses    = add_prefix('_', sesid),
            task    = f"task-{run['bids']['task']}",
            suffix  = run['bids']['suffix'])

    elif modality == 'pet':

        # bidsname: sub-<participant_label>[_ses-<session_label>]_task-<task_label>[_acq-<label>][_rec-<label>][_run-<index>]_suffix
        bidsname = '{sub}{_ses}_{task}{_acq}{_rec}{_run}_{suffix}'.format(
            sub     = subid,
            _ses    = add_prefix('_', sesid),
            task    = f"task-{run['bids']['task']}",
            _acq    = add_prefix('_acq-', run['bids']['acq']),
            _rec    = add_prefix('_rec-', run['bids']['rec']),
            _run    = add_prefix('_run-', runindex),
            suffix  = run['bids']['suffix'])

    elif modality == unknownmodality or modality == ignoremodality:

        # bidsname: sub-<participant_label>[_ses-<session_label>]_acq-<label>[..][_suffix]
        bidsname = '{sub}{_ses}{_task}_{acq}{_ce}{_rec}{_dir}{_run}{_echo}{_mod}{_suffix}'.format(
            sub     = subid,
            _ses    = add_prefix('_', sesid),
            _task   = add_prefix('_task-', run['bids']['task']),
            acq     = f"acq-{run['bids']['acq']}",
            _ce     = add_prefix('_ce-',   run['bids']['ce']),
            _rec    = add_prefix('_rec-',  run['bids']['rec']),
            _dir    = add_prefix('_dir-',  run['bids']['dir']),
            _run    = add_prefix('_run-',  runindex),
            _echo   = add_prefix('_echo-', run['bids']['echo']),
            _mod    = add_prefix('_mod-',  run['bids']['mod']),
            _suffix = add_prefix('_',      run['bids']['suffix']))

    else:
        raise ValueError(f'Critical error: modality "{modality}" not implemented, please inform the developers about this error')

    return bidsname


def get_dynamic_value(bidsvalue: str, sourcefile: str) -> str:
    """
    Replaces (dynamic) bidsvalues with (DICOM) run attributes when they start with '<' and end with '>',
    but not with '<<' and '>>'

    :param bidsvalue:   The value from the BIDS key-value pair
    :param sourcefile:  The source (DICOM) file from which the attribute is read
    :return:            Updated bidsvalue (if possible, otherwise the original bidsvalue is returned)
    """

    # Intelligent filling of the value is done runtime by bidscoiner
    if not bidsvalue or not isinstance(bidsvalue, str) or bidsvalue.startswith('<<') and bidsvalue.endswith('>>'):
        return bidsvalue

    # Fill any bids-label with the <annotated> dicom attribute
    if bidsvalue.startswith('<') and bidsvalue.endswith('>'):
        dicomvalue = get_dicomfield(bidsvalue[1:-1], sourcefile)
        if not dicomvalue:
            return bidsvalue
        else:
            bidsvalue = cleanup_value(dicomvalue)

    return bidsvalue


def get_bidsvalue(bidsname: str, bidskey: str, newvalue: str= '') -> str:
    """
    Sets the bidslabel, i.e. '*_bidskey-*_' is replaced with '*_bidskey-bidsvalue_'. If the key is not in the bidsname
    then the newvalue is appended to the acquisition label. If newvalue is empty (= default), then the parsed existing
    bidsvalue is returned and nothing is set

    :param bidsname:    The bidsname (e.g. as returned from get_bidsname or fullpath)
    :param bidskey:     The name of the bidskey, e.g. 'echo'
    :param newvalue:    The new bidsvalue
    :return:            The bidsname with the new bidsvalue or, if newvalue is empty, the existing bidsvalue
    """

    newvalue = cleanup_value(newvalue)
    pathname = os.path.dirname(bidsname)
    bidsname = os.path.basename(bidsname)

    # Get the existing bidsvalue
    oldvalue = ''
    acqvalue = ''
    for label in bidsname.split('_'):
        if '-' in str(label):
            key, value = str(label).split('-', 1)
            if key == bidskey:
                oldvalue = value
            if key == 'acq':
                acqvalue = value

    # Replace the existing bidsvalue with the new value or append the newvalue to the acquisition value
    if newvalue:
        if f'_{bidskey}-' not in bidsname:
            bidskey  = 'acq'
            oldvalue = acqvalue
            newvalue = acqvalue + newvalue
        return os.path.join(pathname, bidsname.replace(f'{bidskey}-{oldvalue}', f'{bidskey}-{newvalue}'))

    # Or just return the parsed old bidsvalue
    else:
        return oldvalue


def increment_runindex(bidsfolder: str, bidsname: str, ext: str='.*') -> str:
    """
    Checks if a file with the same the bidsname already exists in the folder and then increments the runindex (if any)
    until no such file is found

    :param bidsfolder:  The full pathname of the bidsfolder
    :param bidsname:    The bidsname with a provisional runindex
    :param ext:         The file extension for which the runindex is incremented (default = '.*')
    :return:            The bidsname with the incremented runindex
    """

    while glob.glob(os.path.join(bidsfolder, bidsname + ext)):

        runindex = get_bidsvalue(bidsname, 'run')
        if runindex:
            bidsname = get_bidsvalue(bidsname, 'run', int(runindex) + 1)

    return bidsname
