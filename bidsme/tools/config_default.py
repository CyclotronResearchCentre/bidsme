###############################################################################
# config_default.py provides default values for configuration of BIDSme
###############################################################################
# Copyright (c) 2019-2020, University of Liège
# Author: Nikita Beliy
# Owner: Liege University https://www.uliege.be
# Credits: [Marcel Zwiers]
# Maintainer: Nikita Beliy
# Email: Nikita.Beliy@uliege.be
# Status: developpement
###############################################################################
# This file is part of BIDSme
# BIDSme is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
# eegBidsCreator is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with BIDSme.  If not, see <https://www.gnu.org/licenses/>.
##############################################################################


config = {
        # Used bidsmap files
        "maps": {
            # name for template used by bidsmapper
            "template": "bidsmap_template.yaml",
            # name for main map file used by bidscoiner
            "map": "bidsmap.yaml"
            },
        # Configuration of skipping subjects and sessions
        "selection": {
            "skip_tsv": False,
            "skip_existing": False,
            "skip_session": False
            },
        # Configuration realted to logging
        "logging": {
            # silence stdout output
            "quiet": False,
            "level": "INFO",
            "format": '%(name)s(%(lineno)d) - %(levelname)s %(message)s'
            },
        # list of plugins to use
        "plugins": {
            # plugin for preparation stage
            "prepare": {
                # path to the file
                "path": "",
                # dictionary of named options passed to plugin
                "options": {}
                },
            # plugin for bidsification
            "bidsify": {
                "path": "",
                "options": {}
                },
            # plugin for processing
            "process": {
                "path": "",
                "options": {}
                },
            # plugin for mapping, if not set, one for bidsification is used
            "map": {
                "path": "",
                "options": {}
                }
            },
        # configuration for preparation stage
        "prepare": {
            # prefixes to identify subject and session folders
            "sub_prefix": "",
            "ses_prefix": "",
            # switches to indicate that there no subject and/or session
            # folders
            "no_subject": False,
            "no_session": False,
            # dictionary for folders with data and corresponding data type
            # for. ex. {"nii": "MRI"}
            "rec_folders": {},
            # Path to template json file defining subject tsv columns
            "part_template": None
            },
        "process": {
            # Path to template json file defining subject tsv columns
            "part_template": None
            },
        "bidsify": {
            # Path to template json file defining subject tsv columns
            "part_template": None
            }
        }
