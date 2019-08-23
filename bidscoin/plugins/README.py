"""
This function contains placeholder code demonstrating the bidscoin plugin API, both for bidsmapper.py and for
bidscoiner.py. Enter the name of this module (default location is the plugins-folder; otherwise the full path
must be provided) in the bidsmap dictionary file to import the plugin functions in this module, e.g. "README.py"
or "myplugin.py". The functions in this module should be named "bidsmapper_plugin" for bidsmapper.py and
"bidscoiner_plugin" for bidscoiner.py. See the code for the (positional) input arguments of the plugin-functions.
"""


import os
import logging


LOGGER = logging.getLogger(f'bidscoin.{os.path.splitext(os.path.basename(__file__))[0]}')


def bidsmapper_plugin(seriesfolder: str, bidsmap: dict, heuristics: dict) -> dict:
    """
    The plugin to map info onto bids labels

    :param seriesfolder:    The full-path name of the raw-data series folder
    :param bidsmap:         The bidsmap
    :param heuristics:      Full BIDS heuristics data structure, with all options, BIDS labels and attributes, etc
    :return:                The bidsmap with new entries in it
    """

    LOGGER.debug(f'This is a bidsmapper demo-plugin working on: {seriesfolder}')
    return bidsmap


def bidscoiner_plugin(session: str, bidsmap: dict, bidsfolder: str, personals: dict) -> None:
    """
    The plugin to cast the series into the bids folder

    :param session:     The full-path name of the subject/session raw data source folder
    :param bidsmap:     The full mapping heuristics from the bidsmap YAML-file
    :param bidsfolder:  The full-path name of the BIDS root-folder
    :param personals:   The dictionary with the personal information
    :return:            Nothing
    """

    LOGGER.debug(f'This is a bidscoiner demo-plugin working on: {session} -> {bidsfolder}')
