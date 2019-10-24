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
from importlib import util
from ruamel.yaml import YAML
from tools import tools


yaml = YAML()

# yaml.add_representer(str, str_presenter)
yaml.indent(mapping=2, sequence=4, offset=2)
yaml.preserve_quotes = True

logger = logging.getLogger(__name__)
# NB: get_matching_run() uses this order to search for a match
bidsmodalities = ('fmap', 'anat', 'func', 'dwi', 'beh', 'pet')
ignoremodality = 'leave_out'
unknownmodality = 'extra_data'
# This is not really something from BIDS, but these are 
# the BIDS-labels used in the bidsmap
bidslabels = ('task', 'acq', 'ce', 'rec', 'dir', 'run',
              'mod', 'echo', 'suffix', 'IntendedFor')


def bidsversion() -> str:
    """
    Reads the BIDS version from the BIDSVERSION.TXT file

    :return:    The BIDS version number
    """

    with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                           'bidsversion.txt')) as fid:
        version = fid.read().strip()

    return str(version)


def version() -> str:
    """
    Reads the BIDSCOIN version from the VERSION.TXT file

    :return:    The BIDSCOIN version number
    """

    with open(os.path.join(os.path.dirname(os.path.dirname(__file__)),
                           'version.txt')) as fid:
        version = fid.read().strip()

    return str(version)


def setup_logging(log_file: str, debug: bool=False) -> logging.Logger:
    """
    Setup the logging

    :param log_file:    Name of the logfile
    :param debug:       Set log level to DEBUG if debug==True
    :return:            Logger object
     """
    # Create the log dir if it does not exist
    logdir = os.path.dirname(log_file)
    os.makedirs(logdir, exist_ok=True)

    # Derive the name of the error logfile from the normal log_file
    error_file = os.path.splitext(log_file)[0] + '.errors'

    # Set the format and logging level
    fmt = '%(asctime)s - %(name)s - %(levelname)s %(message)s'
    datefmt = '%Y-%m-%d %H:%M:%S'
    formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)
    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    # Set & add the streamhandler and 
    # add some color to those boring terminal logs! :-)
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
                logger.info(f"The following BIDScoin errors and "
                            "warnings were reported:\n\n{40*'>'}"
                            "\n{errors}{40*'<'}\n")

            else:
                logger.info(f'No BIDScoin errors or warnings were reported')
                logger.info('')

        elif filehandler.name == 'loghandler':
            logfile = filehandler.baseFilename

    logger.info(f'For the complete log see: {logfile}')
    logger.info("NB: logfiles may contain identifiable information, "
                "e.g. from pathnames")


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


def import_plugin(plugin: str):
    """

    :param plugin:  Name of the plugin
    :return:        plugin-module
    """

    # Get the full path to the plugin-module
    if os.path.basename(plugin) == plugin:
        plugin = os.path.join(os.path.dirname(__file__), 'plugins', plugin)
    else:
        plugin = plugin
    plugin = os.path.abspath(os.path.realpath(os.path.expanduser(plugin)))

    # See if we can find the plug-in
    if not os.path.isfile(plugin):
        logger.error(f"Could not find plugin: '{plugin}'")
        return None

    # Load the plugin-module
    try:
        spec = util.spec_from_file_location('bidscoin_plugin', plugin)
        module = util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # bidsmapper -> module.bidsmapper_plugin(runfolder, 
        #                                        bidsmap_new, bidsmap_old)
        if 'bidsmapper_plugin' not in dir(module):
            logger.info('Could not find bidscoiner_plugin() in ' + plugin)

        # bidscoiner -> module.bidscoiner_plugin(session, bidsmap, 
        #                                        bidsfolder, personals)
        if 'bidscoiner_plugin' not in dir(module):
            logger.info('Could not find bidscoiner_plugin() in ' + plugin)

        if 'bidsmapper_plugin' not in dir(module) and \
                'bidscoiner_plugin' not in dir(module):
            logger.warning("{} can (and will) not perform any operation"
                           .format(plugin))

        return module

    except Exception:
        logger.exception(f"Could not import '{plugin}'")

        return None


def test_tooloptions(tool: str, opts: dict) -> bool:
    """
    Performs tests of the user tool parameters set in bidsmap['Options']

    :param tool:    Name of the tool that is being tested in bidsmap['Options']
    :param opts:    The editable options belonging to the tool
    :return:        True if the tool generated the expected result, 
                    False if there was a tool error
    """

    if tool == 'dcm2niix':
        command = f"{opts['path']}dcm2niix -h"
    elif tool == 'bidscoin':
        command = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                               'bidscoin.py -v')
    else:
        logger.warning(f"Testing of '{tool}' not supported")
        return None

    logger.info(f"Testing: '{tool}'")

    return run_command(command)


def test_plugins(plugin: str='') -> bool:
    """
    Performs tests of the plug-ins in bidsmap['PlugIns']

    :param plugin:  The name of the plugin that is being tested 
                    (-> bidsmap['Plugins'])
    :return:        True if the plugin generated the expected result, 
                    False if there was a plug-in error, 
                    None if this function has an implementation error
    """

    logger.info(f"Testing: '{plugin}' plugin")

    module = import_plugin(plugin)
    if inspect.ismodule(module):
        methods = [method for method in dir(module) 
                   if not method.startswith('_')]
        logger.info(f"Result:\n{module.__doc__}\n{plugin} "
                    "attributes and methods:\n{methods}\n")
        return True

    else:
        return False


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


def load_bidsmap(yamlfile: str='',
                 folder: str='', 
                 report: bool=True) -> (dict, str):
    """
    Read the mapping heuristics from the bidsmap yaml-file. 
    If yamlfile is not fullpath, then 'folder' is first searched before
    the default 'heuristics'. If yamfile is empty, then first 'bidsmap.yaml' 
    is searched for, them 'bidsmap_template.yaml'. So fullpath has precendence 
    over folder and bidsmap.yaml has precedence over bidsmap_template.yaml

    :param yamlfile:    The full pathname or basename of the bidsmap yaml-file. 
                        If None, the default bidsmap_template.yaml file 
                        in the heuristics folder is used
    :param folder:      Only used when yamlfile=basename or None: 
                        yamlfile is then first searched for in folder 
                        and then falls back to the ./heuristics folder 
                        (useful for centrally managed template yaml-files)
    :param report:      Report log.info when reading a file
    :return:            Tuple with (1) ruamel.yaml dict structure, 
                        with all options, BIDS mapping heuristics, 
                        labels and attributes, etc 
                        and (2) the fullpath yaml-file
    """

    # Input checking
    heuristics_folder = os.path.join(os.path.dirname(__file__),
                                     '..','heuristics')
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

    yamlfile = os.path.abspath(os.path.realpath(os.path.expanduser(yamlfile)))
    if not os.path.isfile(yamlfile):
        if report:
            logger.info('No existing bidsmap file found: {}'
                        .format(os.path.abspath(yamlfile)))
        return dict(), yamlfile
    elif report:
        logger.info('Reading: ' + os.path.abspath(yamlfile))

    # Read the heuristics from the bidsmap file
    with open(yamlfile, 'r') as stream:
        bidsmap = yaml.load(stream)

    # Issue a warning if the version in the bidsmap YAML-file 
    # is not the same as the bidscoin version
    if 'bidscoin' in bidsmap['Options'] \
            and 'version' in bidsmap['Options']['bidscoin']:
        bidsmapversion = bidsmap['Options']['bidscoin']['version']
    elif 'version' in bidsmap['Options']:
        bidsmapversion = bidsmap['Options']['version']
    else:
        bidsmapversion = 'Unknown'

    if bidsmapversion != version() and report:
        logger.warning('BIDScoiner version conflict: '
                       '{} was created using version {}, '
                       'but this is version {}'
                       .format(yamlfile, bidsmapversion, version())
                       )

    # Make sure we get a proper list of plugins
    if not bidsmap['PlugIns']:
        bidsmap['PlugIns'] = []
    bidsmap['PlugIns'] = [plugin for plugin in bidsmap['PlugIns'] if plugin]

    return bidsmap, yamlfile

def tr(s):
    return s.replace('\\', '\\\\')

def save_bidsmap(filename: str, bidsmap: dict):
    """
    Save the BIDSmap as a YAML text file

    :param filename:
    :param bidsmap:         Full bidsmap data structure, with all options, 
                            BIDS labels and attributes, etc
    :return:
    """

    logger.info('Writing bidsmap to: ' + filename)
    with open(filename, 'w') as stream:
        yaml.dump(bidsmap, stream, transform=tr)


    # See if we can reload it, i.e. whether it is valid yaml...
    try:
        load_bidsmap(filename, '', False)
    except Exception:
        # Just trying again seems to help? :-)
        with open(filename, 'w') as stream:
            yaml.dump(bidsmap, stream)
        try:
            load_bidsmap(filename, '', False)
        except Exception:
            logger.error('The saved output bidsmap does not seem to be '
                         'valid YAML, please check {}, e.g. by way of '
                         'an online yaml validator, '
                         'such as https://yamlchecker.com/'
                         .format(filename)
                         )


def add_prefix(prefix: str, tag: str) -> str:
    """
    Simple function to account for optional BIDS tags in the bids file names, 
    i.e. it prefixes 'prefix' only when tag is not empty

    :param prefix:  The prefix (e.g. '_sub-')
    :param tag:     The tag (e.g. 'control01')
    :return:        The tag with the leading prefix (e.g. '_sub-control01') 
                    or just the empty tag ''
    """

    if tag:
        tag = prefix + str(tag)
    else:
        tag = ''

    return tag


def strip_suffix(run: dict) -> dict:
    """
    Certain attributes such as SeriesDescriptions (but not ProtocolName!?) 
    may get a suffix like '_SBRef' from the vendor,
    try to strip it off from the BIDS labels

    :param run: The run with potentially added suffixes that are the same 
                as the BIDS suffixes
    :return:    The run with these suffixes removed
    """

    # See if we have a suffix for this modality
    if 'suffix' in run['bids'] and run['bids']['suffix']:
        suffix = run['bids']['suffix'].lower()
    else:
        return run

    # See if any of the BIDS labels ends with the same suffix. 
    # If so, then remove it
    for key in run['bids']:
        if key == 'suffix':
            continue
        if isinstance(run['bids'][key], str) and \
                run['bids'][key].lower().endswith(suffix):
            # NB: This will leave the added '_' and '.' characters, 
            # but they will be taken out later (as they are not BIDS-valid)
            run['bids'][key] = run['bids'][key][0:-len(suffix)]

    return run


def dir_bidsmap(bidsmap: dict, source: str) -> list:
    """
    Make a provenance list of all the runs in the bidsmap[source]

    :param bidsmap: The bidsmap, with all the runs in it
    :param source:  The information source in the bidsmap that is used, 
                    e.g. 'DICOM'
    :return:        List of all provenances
    """

    provenance = []
    for modality in bidsmap[source]:
        if modality in ("subject", "session"):
            continue
        if bidsmap[source][modality]:
            for run in bidsmap[source][modality]:
                provenance.append(run['provenance'])
                if not run['provenance']:
                    logger.warning(f'The bidsmap run {modality} run does '
                                   'not contain provenance data')
    provenance.sort()
    return provenance


def get_run(bidsmap: dict, source: str, 
            modality, suffix_idx, 
            recording=None) -> dict:
    """
    Find the (first) run in bidsmap[source][bidsmodality] 
    with run['bids']['suffix_idx'] == suffix_idx

    :param bidsmap:     This could be a template bidsmap, with all options,
                        BIDS labels and attributes, etc
    :param source:      The information source in the bidsmap that is used,
                        e.g. 'DICOM'
    :param modality:    The modality in which a matching run is searched for 
                        (e.g. 'anat')
    :param suffix_idx:  The name of the suffix that is searched for 
                        (e.g. 'bold') or the modality index number
    :param dicomfile:   The name of the dicomfile. If given, the DICOM values 
                        are read from file
    :return:            The clean (filled) run item in 
                        the bidsmap[source][bidsmodality] 
                        with the matching suffix_idx, otherwise None
    """

    for index, run in enumerate(bidsmap[source][modality]):
        if index == suffix_idx or run['bids']['suffix'] == suffix_idx:

            run_ = dict(provenance={}, attributes={}, bids={})

            for attrkey, attrvalue in run['attributes'].items():
                if recording:
                    run_['attributes'][attrkey] = recording.get_field(attrkey)
                    run_['provenance'] = recording.currentFile()
                else:
                    run_['attributes'][attrkey] = attrvalue

            for bidskey, bidsvalue in run['bids'].items():
                if recording:
                    run_['bids'][bidskey] = \
                            recording.get_dynamic_field(bidsvalue)
                else:
                    run_['bids'][bidskey] = bidsvalue

            return run_

    logger.error(f"'{modality}' run with suffix_idx '{suffix_idx}' "
                 "not found in bidsmap['{source}']")


def delete_run(bidsmap: dict, 
               source: str, 
               modality: str,
               provenance: str) -> dict:
    """
    Delete a run from the BIDS map

    :param bidsmap:     Full bidsmap data structure, with all options, 
                        BIDS labels and attributes, etc
    :param source:      The information source in the bidsmap that is used, 
                        e.g. 'DICOM'
    :param modality:    The modality in the source that is used, e.g. 'anat'
    :param provenance:  The unique provance that is use to identify the run
    :return:            The new bidsmap
    """

    for index, run in enumerate(bidsmap[source][modality]):
        if run['provenance'] == provenance:
            del bidsmap[source][modality][index]

    return bidsmap


def append_run(bidsmap: dict, source: str, modality: str,
               run: dict, clean: bool=True) -> dict:
    """
    Append a run to the BIDS map

    :param bidsmap:     Full bidsmap data structure, with all options,
                        BIDS labels and attributes, etc
    :param source:      The information source in the bidsmap that is used,
                        e.g. 'DICOM'
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


def update_bidsmap(bidsmap: dict, source_modality: str,
                   provenance: str, target_modality: str,
                   run: dict, source: str= 'DICOM', clean: bool=True) -> dict:
    """
    Update the BIDS map if the modality changes:
    1. Remove the source run from the source modality section
    2. Append the (cleaned) target run to the target modality section

    Else:
    1. Use the provenance to look-up the index number in that modality
    2. Replace the run

    :param bidsmap:             Full bidsmap data structure, with all options, 
                                BIDS labels and attributes, etc
    :param source_modality:     The current modality name, e.g. 'anat'
    :param provenance:          The unique provance that is use 
                                to identify the run
    :param target_modality:     The modality name what is should be, e.g. 'dwi'
    :param run:                 The run item that is being moved
    :param source:              The name of the information source, 
                                e.g. 'DICOM'
    :param clean:               A boolean that is passed to bids.append_run 
                                (telling it to clean-up commentedMap fields)
    :return:
    """

    num_runs_in = len(dir_bidsmap(bidsmap, source))

    # Warn the user if the target run already exists 
    # when the run is moved to another modality
    if source_modality != target_modality:
        if exist_run(bidsmap, source, target_modality, run):
            logger.warning(f'That run from {source_modality} already '
                           'exists in {target_modality}...')

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
        logger.error(f"Number of runs in bidsmap['{source}'] "
                     "changed unexpectedly: {num_runs_in} -> {num_runs_out}")

    return bidsmap


def match_attribute(longvalue, values) -> bool:
    """
    Compare the value items with / without *wildcard* 
    with the longvalue string. If both longvalue
    and values are a list then they are directly compared as is

    Examples:
        match_attribute('my_pulse_sequence_name', 'name') -> False
        match_attribute('my_pulse_sequence_name', '*name*') -> True
        match_attribute('T1_MPRAGE', '['T1w', 'MPRAGE']') -> False
        match_attribute('T1_MPRAGE', '['T1w', 'T1_MPRAGE']') -> True
        match_attribute('T1_MPRAGE', '['*T1w*', '*MPRAGE*']') -> True

    :param longvalue:   The long string that is being searched in
    :param values:      Either a list with search items or a string 
                        that is matched one-to-one
    :return:            True if a match is found or both longvalue 
                        and values are identical or
                        empty / None. False otherwise
    """
    if isinstance(values, list):
        for val in values:
            if tools.match_value(longvalue, val):
                return True
        return False
    return tools.match_value(longvalue, values)


def exist_run(bidsmap: dict, source: str, modality: str,
              run_item: dict, matchbidslabels: bool=False) -> bool:
    """
    Checks if there is already an entry in runlist 
    with the same attributes and, optionally, 
    bids values as in the input run

    :param bidsmap:         Full bidsmap data structure, with all options,
                            BIDS labels and attributes, etc
    :param source:          The information source in the bidsmap that is used,
                            e.g. 'DICOM'
    :param modality:        The modality in the source that is used, 
                            e.g. 'anat'
                            Empty values will search through all modalities
    :param run_item:        The run (listitem) that is searched for 
                            in the modality
    :param matchbidslabels: If True, also matches the BIDS-labels, 
                            otherwise only run['attributes']
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
        match = any([run_item['attributes'][key] is not None 
                     for key in run_item['attributes']])

        # Search for a case where all run_item items 
        # match with the run_item items
        for itemkey, itemvalue in run_item['attributes'].items():
            # Matching bids-labels which exist in one modality 
            # but not in the other -> None
            value = run['attributes'].get(itemkey, None)   
            match = match and match_attribute(itemvalue, value)
            if not match:
                # There is no point in searching further within 
                # the run_item now that we've found a mismatch
                break                                       

        # See if the bidslabels also all match. This is probably 
        # not very useful, but maybe one day...
        if matchbidslabels and match:
            for itemkey, itemvalue in run_item['bids'].items():
                # Matching bids-labels which exist in one modality 
                # but not in the other -> None
                value = run['bids'].get(itemkey, None)      
                match = match and value == itemvalue
                if not match:
                    # There is no point in searching further within 
                    # the run_item now that we've found a mismatch
                    break                                   

        # Stop searching if we found a matching run_item 
        # (i.e. which is the case if match is still True after all run tests).
        # TODO: maybe count how many instances, could perhaps be useful info
        if match:
            return True

    return False


def get_matching_run(recording, bidsmap: dict, 
                     modalities: tuple = bidsmodalities 
                     + (ignoremodality, unknownmodality)
                     ) -> tuple:
    """
    Find the first run in the bidsmap with dicom attributes 
    that match with the dicom file. 
    Then update the (dynamic) bids values 
    (values are cleaned-up to be BIDS-valid)

    :param dicomfile:   The full pathname of the dicom-file
    :param bidsmap:     Full bidsmap data structure, with all options,
                        BIDS labels and attributes, etc
    :param modalities:  The modality in which a matching run is searched for. 
                        Default = bidsmodalities + 
                        (ignoremodality, unknownmodality)
    :return:            (run, modality, index) The matching and filled-in 
                        /cleaned run item, modality and list index as in 
                        run = bidsmap[DICOM][modality][index]
                        modality = bids.unknownmodality and index = None 
                        if there is no match, the run is still populated 
                        with info from the dicom-file
    """

    source = recording.type
    modalities = recording.bidsmodalities + (ignoremodality, unknownmodality)
    run_ = dict(provenance={}, attributes={}, bids={})

    # Loop through all bidsmodalities and runs; all info goes into run_
    for modality in modalities:
        if modality not in bidsmap[source]: 
            logger.warning("{}: Missing {} modality"
                           .format(source, modality))
            continue

        if bidsmap[source][modality] is None: continue

        for index, run in enumerate(bidsmap[source][modality]):
            # The CommentedMap API is not guaranteed for the future 
            # so keep this line as an alternative
            run_ = dict(provenance={}, attributes={}, bids={})
            # Normally match==True, but make match==False 
            # if all attributes are empty
            match = any([run['attributes'][attrkey] is 
                         not None 
                         for attrkey in run['attributes']])

            # Try to see if the dicomfile matches all of 
            # attributes and fill all of them
            for attrkey, attrvalue in run['attributes'].items():

                # Check if the attribute value matches with 
                # the info from the dicomfile
                dicomvalue = recording.get_field(attrkey)
                if attrvalue:
                    match = match and match_attribute(dicomvalue, attrvalue)

                # Fill the empty attribute with the info from the dicomfile
                run_['attributes'][attrkey] = dicomvalue

            # Try to fill the bids-labels
            for bidskey, bidsvalue in run['bids'].items():

                # Replace the dynamic bids values
                run_['bids'][bidskey] = recording.get_dynamic_field(bidsvalue)

                # SeriesDescriptions (and ProtocolName?) may get a suffix 
                # like '_SBRef' from the vendor, try to strip it off
                run_ = strip_suffix(run_)

            # Stop searching the bidsmap if we have a match. 
            # TODO: check if there are more matches (i.e. conflicts)
            if match:
                run_['provenance'] = recording.currentFile()
                return run_, modality, index

    # We don't have a match (all tests failed, 
    # so modality should be the *last* one, 
    # i.e. unknownmodality)
    logger.debug("Could not find a matching run in the bidsmap for {} -> {}"
                 .format(recording.currentFile(), modality))
    run_['provenance'] = recording.currentFile()

    return run_, modality, None


def get_subid_sesid(recording,
                    subid: str='', sesid: str='', 
                    subprefix: str= 'sub-', sesprefix: str= 'ses-'):
    """
    Extract the cleaned-up subid and sesid from the pathname 
    or from the dicom file if subid/sesid == '<<SourceFilePath>>'

    :param dicomfile:   The full pathname of the dicomfile. 
                        If given, the DICOM values are read from the file
    :param subid:       The subject identifier, 
                        i.e. name of the subject folder 
                        (e.g. 'sub-001' or just '001'). Can be left empty
    :param sesid:       The optional session identifier, 
                        i.e. name of the session folder 
                        (e.g. 'ses-01' or just '01')
    :param subprefix:   The optional subprefix (e.g. 'sub-'). 
                        Used to parse the sub-value from 
                        the provenance as default subid
    :param sesprefix:   The optional sesprefix (e.g. 'ses-'). 
                        If it is found in the provenance then 
                        a default sesid will be set
    :return:            Updated (subid, sesid) tuple,
                        including the sub/sesprefix
    """

    # Add default value for subid and sesid (e.g. for the bidseditor)
    dicompath = os.path.dirname(str(recording.currentFile()))
    if subid == '<<SourceFilePath>>':
        subid = dicompath.rsplit(os.sep + subprefix, 1)[1].split(os.sep)[0]
    else:
        subid = recording.get_dynamic_field(subid)
    if sesid == '<<SourceFilePath>>':
        if os.sep + sesprefix in dicompath:
            sesid = dicompath.rsplit(os.sep + sesprefix, 1)[1]\
                    .split(os.sep)[0]
        else:
            sesid = ''
    else:
        sesid = recording.get_dynamic_value(sesid)

    # Add sub- and ses- prefixes if they are not there
    subid = 'sub-' + tools.cleanup_value(re.sub(f'^{subprefix}', '', subid))
    if sesid:
        sesid = 'ses-' + tools.cleanup_value(
                re.sub(f'^{sesprefix}', '', sesid))

    return subid, sesid


def get_bidsname(subid: str, sesid: str,
                 modality: str, 
                 run: dict, runindex: str= '',
                 subprefix: str= 'sub-', sesprefix: str= 'ses-') -> str:
    """
    Composes a filename as it should be according to the BIDS standard 
    using the BIDS labels in run

    :param subid:       The subject identifier,
                        i.e. name of the subject folder
                        (e.g. 'sub-001' or just '001'). Can be left empty
    :param sesid:       The optional session identifier, 
                        i.e. name of the session folder 
                        (e.g. 'ses-01' or just '01'). Can be left empty
    :param modality:    The bidsmodality (choose from bids.bidsmodalities)
    :param run:         The run mapping with the BIDS labels
    :param runindex:    The optional runindex label (e.g. 'run-01'). 
                        Can be left ''
    :param subprefix:   The optional subprefix (e.g. 'sub-'). 
                        Used to parse the sub-value from the provenance 
                        as default subid
    :param sesprefix:   The optional sesprefix (e.g. 'ses-'). 
                        If it is found in the provenance then a default 
                        sesid will be set
    :return:            The composed BIDS file-name (without file-extension)
    """
    assert modality in bidsmodalities + (unknownmodality, ignoremodality)

    # Try to update the sub/ses-ids
    subid, sesid = get_subid_sesid(run['provenance'], subid, sesid, 
                                   subprefix, sesprefix)

    # Validate and do some checks to allow for dragging the run entries 
    # between the different modality-sections
    run = copy.deepcopy(run) # Avoid side effects when changing run
    for bidslabel in bidslabels:
        if bidslabel not in run['bids']:
            run['bids'][bidslabel] = None
        else:
            # TO FIX -- N.B.
            run['bids'][bidslabel] = tools.cleanup_value(
                    get_dynamic_value(run['bids'][bidslabel],
                                      run['provenance']))

    # Use the clean-up runindex
    if not runindex:
        runindex = run['bids']['run']

    # Compose the BIDS filename (-> switch statement)
    if modality == 'anat':

        # bidsname: 
        #   sub-<participant_label>
        #   [_ses-<session_label>]
        #   [_acq-<label>]
        #   [_ce-<label>]
        #   [_rec-<label>]
        #   [_run-<index>]
        #   [_mod-<label>]
        #   _suffix
        bidsname = '{sub}{_ses}{_acq}{_ce}{_rec}{_run}{_mod}_{suffix}'.format(
            sub     = subid,
            _ses    = add_prefix('_', sesid),
            _acq    = add_prefix('_acq-', run['bids']['acq']),
            _ce     = add_prefix('_ce-', run['bids']['ce']),
            _rec    = add_prefix('_rec-', run['bids']['rec']),
            _run    = add_prefix('_run-', runindex),
            _mod    = add_prefix('_mod-', run['bids']['mod']),
            suffix  = run['bids']['suffix'])

    elif modality == 'func':

        # bidsname: 
        #   sub-<label>
        #   [_ses-<label>]
        #   _task-<label>
        #   [_acq-<label>]
        #   [_ce-<label>]
        #   [_dir-<label>]
        #   [_rec-<label>]
        #   [_run-<index>]
        #   [_echo-<index>]
        #   _<contrast_label>.nii[.gz]
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
