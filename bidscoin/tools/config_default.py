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
            }
        }
