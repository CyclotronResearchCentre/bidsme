#!/usr/bin/env python
"""
Creates a bidsmap.yaml YAML file that maps the information from all raw data to the
BIDS labels (see also [bidsmap_template.yaml] and [bidstrainer.py]). You can check
and edit the bidsmap.yaml file before passing it to [bidscoiner.py]
"""

# Global imports (specific modules may be imported when needed)
import os.path
import textwrap
import copy
from ruamel.yaml import YAML
yaml = YAML()
try:
    from bidscoin import bids
except ImportError:
    import bids         # This should work if bidscoin was not pip-installed


def built_dicommap(dicomfile, bidsmap, heuristics, automatic):
    """
    All the logic to map dicom-attributes (fields/tags) onto bids-labels go into this function

    :param str dicomfile:   The full-path name of the source dicom-file
    :param dict bidsmap:    The bidsmap as we had it
    :param dict heuristics: Full BIDS heuristics data structure, with all options, BIDS labels and attributes, etc
    :param bool automatic:  If True, the user will not be asked for help if an unknown series is encountered
    :return:                The bidsmap with new entries in it
    :rtype: dict
    """

    # Input checks
    if not dicomfile or not heuristics['DICOM']:
        return bidsmap

    # Get the matching series
    result   = bids.get_matching_dicomseries(dicomfile, heuristics)
    series   = result['series']
    modality = result['modality']

    # If nothing matched, ask the user for help
    if modality == bids.unknownmodality:
        print('Unknown modality found: ' + dicomfile)
        if not automatic:
            answer = bids.askfor_mapping(heuristics['DICOM'], series, dicomfile)
        if 'answer' in locals() and answer:                                                     # A catch for users canceling the question for help
            series   = answer['series']
            modality = answer['modality']

    # Copy the filled-in attributes series over to the bidsmap
    if bidsmap['DICOM'][modality] is None:
        bidsmap['DICOM'][modality] = [series]
    elif not bids.exist_series(series, bidsmap['DICOM'][modality], matchbidslabels=False):      # NB: the bidsmap may still have annotated labels (which are replaced by their value in the mapped bidsmap)
        bidsmap['DICOM'][modality].append(series)

    return bidsmap


def built_parmap(parfile, bidsmap, heuristics, automatic):
    """
    All the logic to map PAR/REC fields onto bids labels go into this function

    :param str parfile:     The full-path name of the source PAR-file
    :param dict bidsmap:    The bidsmap as we had it
    :param dict heuristics: Full BIDS heuristics data structure, with all options, BIDS labels and attributes, etc
    :param bool automatic:  If True, the user will not be asked for help if an unknown series is encountered
    :return:                The bidsmap with new entries in it
    :rtype: dict
    """

    # Input checks
    if not parfile or not heuristics['PAR']:
        return bidsmap

    # TODO: Loop through all bidsmodalities and series

    return bidsmap


def built_p7map(p7file, bidsmap, heuristics, automatic):
    """
    All the logic to map P*.7-fields onto bids labels go into this function

    :param str p7file:      The full-path name of the source P7-file
    :param dict bidsmap:    The bidsmap as we had it
    :param dict heuristics: Full BIDS heuristics data structure, with all options, BIDS labels and attributes, etc
    :param bool automatic:  If True, the user will not be asked for help if an unknown series is encountered
    :return:                The bidsmap with new entries in it
    :rtype: dict
    """

    # Input checks
    if not p7file or not heuristics['P7']:
        return bidsmap

    # TODO: Loop through all bidsmodalities and series

    return bidsmap


def built_niftimap(niftifile, bidsmap, heuristics, automatic):
    """
    All the logic to map nifti-info onto bids labels go into this function

    :param str niftifile:   The full-path name of the source nifti-file
    :param dict bidsmap:    The bidsmap as we had it
    :param dict heuristics: Full BIDS heuristics data structure, with all options, BIDS labels and attributes, etc
    :param bool automatic:  If True, the user will not be asked for help if an unknown series is encountered
    :return:                The bidsmap with new entries in it
    :rtype: dict
    """

    # Input checks
    if not niftifile or not heuristics['Nifti']:
        return bidsmap

    # TODO: Loop through all bidsmodalities and series

    return bidsmap


def built_filesystemmap(seriesfolder, bidsmap, heuristics, automatic):
    """
    All the logic to map filesystem-info onto bids labels go into this function

    :param seriesfolder:    The full-path name of the source folder
    :param dict bidsmap:    The bidsmap as we had it
    :param dict heuristics: Full BIDS heuristics data structure, with all options, BIDS labels and attributes, etc
    :param bool automatic:  If True, the user will not be asked for help if an unknown series is encountered
    :return:                The bidsmap with new entries in it
    :rtype: dict
    """

    # Input checks
    if not seriesfolder or not heuristics['FileSystem']:
        return bidsmap

    # TODO: Loop through all bidsmodalities and series

    return bidsmap


def built_pluginmap(seriesfolder, bidsmap):
    """
    Call the plugin to map info onto bids labels

    :param seriesfolder: The full-path name of the source folder
    :param dict bidsmap: The bidsmap as we had it
    :return:             The bidsmap with new entries in it
    :rtype: dict
    """

    from importlib import import_module

    # Input checks
    if not seriesfolder or not bidsmap['PlugIn']:
        return bidsmap

    # Import and run the plugins
    for pluginfunction in bidsmap['PlugIn']:
        plugin  = import_module(os.path.join(__file__,'plugins', pluginfunction))
        # TODO: check first if the plug-in function exist
        bidsmap = plugin.bidsmapper(seriesfolder, bidsmap)

    return bidsmap


def bidsmapper(rawfolder, bidsfolder, bidsmapfile='bidsmap_sample.yaml', automatic=False):
    """
    Main function that processes all the subjects and session in the rawfolder
    and that generates a maximally filled-in bidsmap.yaml file in bidsfolder/code.
    Folders in rawfolder are assumed to contain a single dataset.

    :param str rawfolder:       The root folder-name of the sub/ses/data/file tree containing the source data files
    :param str bidsfolder:      The name of the BIDS root folder
    :param str bidsmapfile:     The name of the bidsmap YAML-file
    :param bool automatic:      If True, the user will not be asked for help if an unknown series is encountered
    :return: str bidsmapfile:   The name of the mapped bidsmap YAML-file
    :rtype: str
    """

    # Input checking
    rawfolder  = os.path.abspath(os.path.expanduser(rawfolder))
    bidsfolder = os.path.abspath(os.path.expanduser(bidsfolder))

    # Get the heuristics for creating the bidsmap
    heuristics = bids.get_heuristics(bidsmapfile, os.path.join(bidsfolder,'code'))

    # Create a copy / bidsmap skeleton with no modality entries (i.e. bidsmap with empty lists)
    bidsmap = copy.deepcopy(heuristics)
    for logic in ('DICOM', 'PAR', 'P7', 'Nifti', 'FileSystem'):
        for modality in bids.bidsmodalities + (bids.unknownmodality,):

            if bidsmap[logic] and modality in bidsmap[logic]:
                bidsmap[logic][modality] = None

    # Loop over all subjects and sessions and built up the bidsmap entries
    subjects = bids.lsdirs(rawfolder, 'sub-*')
    for subject in subjects:

        sessions = bids.lsdirs(subject, 'ses-*')
        if not sessions: sessions = subject
        for session in sessions:

            print('Parsing: ' + session)

            for series in bids.lsdirs(session):

                # Update / append the dicom mapping
                if heuristics['DICOM']:
                    dicomfile = bids.get_dicomfile(series)
                    bidsmap   = built_dicommap(dicomfile, bidsmap, heuristics, automatic)

                # Update / append the PAR/REC mapping
                if heuristics['PAR']:
                    parfile   = bids.get_parfile(series)
                    bidsmap   = built_parmap(parfile, bidsmap, heuristics, automatic)

                # Update / append the P7 mapping
                if heuristics['P7']:
                    p7file    = bids.get_p7file(series)
                    bidsmap   = built_p7map(p7file, bidsmap, heuristics, automatic)

                # Update / append the nifti mapping
                if heuristics['Nifti']:
                    niftifile = bids.get_niftifile(series)
                    bidsmap   = built_niftimap(niftifile, bidsmap, heuristics, automatic)

                # Update / append the file-system mapping
                if heuristics['FileSystem']:
                    bidsmap   = built_filesystemmap(series, bidsmap, heuristics, automatic)

                # Update / append the plugin mapping
                if heuristics['PlugIn']:
                    bidsmap   = built_pluginmap(series, bidsmap)

    # Create the bidsmap YAML-file in bidsfolder/code
    os.makedirs(os.path.join(bidsfolder,'code'), exist_ok=True)
    bidsmapfile = os.path.join(bidsfolder,'code','bidsmap.yaml')

    # Save the bidsmap to the bidsmap YAML-file
    print('Writing bidsmap to: ' + bidsmapfile)
    with open(bidsmapfile, 'w') as stream:
        yaml.dump(bidsmap, stream)

    return bidsmapfile


# Shell usage
if __name__ == "__main__":

    # Parse the input arguments and run bidsmapper(args)
    import argparse
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=textwrap.dedent(__doc__),
                                     epilog='examples:\n'
                                            '  bidsmapper.py /project/foo/raw /project/foo/bids\n'
                                            '  bidsmapper.py /project/foo/raw /project/foo/bids bidsmap_dccn\n ')
    parser.add_argument('sourcefolder',     help='The source folder containing the raw data in sub-#/ses-#/series format')
    parser.add_argument('bidsfolder',       help='The destination folder with the bids data structure')
    parser.add_argument('bidsmap',          help='The bidsmap YAML-file with the BIDS heuristics (optional argument, default: bidsfolder/code/bidsmap_sample.yaml)', nargs='?', default='bidsmap_sample.yaml')
    parser.add_argument('-a','--automatic', help='If this flag is given the user will not be asked for help if an unknown series is encountered', action='store_true')
    args = parser.parse_args()

    bidsmapfile = bidsmapper(args.sourcefolder, args.bidsfolder, args.bidsmap, args.automatic)
