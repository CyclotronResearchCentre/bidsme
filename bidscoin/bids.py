#!/usr/bin/env python
"""
Module with helper functions

Some functions are derived from dac2bids.py from Daniel Gomez 29.08.2016
https://github.com/dangom/dac2bids/blob/master/dac2bids.py

@author: Marcel Zwiers
"""

# Global imports
import os.path
import glob
import inspect
import re
import logging
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

    return bidsmap, yamlfile


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
        yaml.dump(bidsmap, stream)

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


def dir_bidsmap(bidsmap: dict, source: str="") -> list:
    """
    Make a provenance list of all the runs in the bidsmap[source]

    :param bidsmap: The bidsmap, with all the runs in it
    :param source:  The information source in the bidsmap that is used, 
                    e.g. 'DICOM'
    :return:        List of all provenances
    """

    provenance = []
    if source == "":
        for source in bidsmap:
            if source in ("Options", "PlugIns"):
                continue
            for modality in bidsmap[source]:
                if modality in ("subject", "session"):
                    continue
                if bidsmap[source][modality]:
                    for run in bidsmap[source][modality]:
                        provenance.append(run['provenance'])
                        if not run['provenance']:
                            logger.warning(f'The bidsmap run {modality} run does '
                                           'not contain provenance data')
    else:
        if source not in bidsmap or not bidsmap[source]:
            logger.error("Can't find '{}' in bidsmap")
            return provenance
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


def append_run(recording, bidsmap: dict) -> dict:
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
    run = dict(provenance="", attributes={}, bids={})

    run['provenance'] = recording.currentFile()
    run["bids"] = {lbl: val for lbl, val 
                   in zip(recording.bidsmodalities[recording.modality],
                          recording.labels)}
    run["bids"]["suffix"] = recording.suffix

    if len(recording.main_attributes) > 0:
        for key in recording.main_attributes:
            run['attributes'][key] = recording.get_attribute(key)
    else:
        for key, value in recording.attributes.items():
            run['attributes'][key] = value

    if bidsmap[recording.type][recording.modality] is None:
        bidsmap[recording.type][recording.modality] = [run]
    else:
        bidsmap[recording.type][recording.modality].append(run)
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


def exist_run(recording,
              bidsmap: dict,
              matchbidslabels: bool=False) -> bool:
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
    modality = recording.modality
    t_name = recording.type
    if modality not in bidsmap[t_name] or not bidsmap[t_name][modality]:
        return False
    res = False
    for run in bidsmap[t_name][modality]:
        if run == "subject" or run == "session":
            continue
        match_one = False
        match_all = True
        # Search for a case where all run_item items 
        # match with the run_item items
        for itemkey, itemvalue in run['attributes'].items():
            if recording.get_attribute(itemkey) == itemvalue:
                match_one = True
            else:
                match_all = False
                break
        res = match_one and match_all

        # See if the bidslabels also all match. This is probably 
        # not very useful, but maybe one day...
        if matchbidslabels and res:
            match_one = False
            match_all = True
            for itemkey, itemvalue in run['bids'].items():
                if itemkey not in recording.bidsmodalities:
                    logger.warning("{}:{}: BIDS label {} not a valid label"
                                   .format(recording.type, recording.modality,
                                           itemkey))
                    continue
                # Matching bids-labels which exist in one modality 
                # but not in the other -> None
                if recording.get_label(itemkey) == itemvalue:
                    match_one = True
                else:
                    match_all = False
        res = match_one and match_all

    return res


def get_matching_run(recording, bidsmap: dict) -> int:
    """
    Find the first run in the bidsmap with dicom attributes 
    that match with the dicom file. 
    Then update the (dynamic) bids values 
    (values are cleaned-up to be BIDS-valid)

    :param dicomfile:   The full pathname of the dicom-file
    :param bidsmap:     Full bidsmap data structure, with all options,
                        BIDS labels and attributes, etc
    :return:            (run, modality, index) The matching and filled-in 
                        /cleaned run item, modality and list index as in 
                        run = bidsmap[DICOM][modality][index]
                        modality = bids.unknownmodality and index = None 
                        if there is no match, the run is still populated 
                        with info from the dicom-file
    """
    recording.set_labels("")
    run_id = -1

    # Loop through all bidsmodalities and runs; all info goes into run_
    for modality in recording.bidsmodalities:
        if modality not in bidsmap: 
            logger.warning("{}: Missing {} modality"
                           .format(recording.type, modality))
            continue
        if bidsmap[modality] is None: continue

        for index, run in enumerate(bidsmap[modality]):
            if recording.match_run(run):
                recording.set_labels(modality, bidsmap[modality][index])
                recording.set_main_attributes(bidsmap[modality][index])
                run_id = index
                break

    if recording.modality == recording.unknownmodality:
        if recording.ignoremodality in bidsmap and bidsmap[recording.ignoremodality]:
            for index, run in enumerate(bidsmap[recording.ignoremodality]):
                if recording.match_run(run):
                    recording.modality = recording.unknownmodality
                    run_id = index
                    break

    if recording.modality == recording.unknownmodality:
        logger.debug("Could not find a matching run in the bidsmap for {} -> {}"
                     .format(recording.currentFile(), modality))
    return run_id


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
    dicompath = os.path.dirname(recording.rec_path)
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
