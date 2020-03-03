config = {
        # Used bidsmap files
        "maps": {
            # name for template used by bidsmapper
            "template": "bidsmap_template.yaml",
            # name for main map file used by bidscoiner
            "map": "bidsmap.yaml"
            },
        # list of plugins to use
        "plugins": {
            # plugin for preparation stage
            "preparation":{
                # path to the file
                "path": None,
                # dictionary of named options passed to plugin
                "options": None
                },
            # plugin for mapping, if not set, one for bidsification is used
            "mapping":{
                "path": None,
                "options": None
                },
            # plugin for bidsification
            "bidsification":{
                "path": None,
                "options": None
                }
            },
        # configuration for preparation stage
        "preparation": {
            # prefixes to identify subject and session folders
            "sub_prefix": "",
            "ses_prefix": "",
            # switches to indicate that there no subject and/or session
            # folders
            "no_subject": False,
            "no_session": False,
            # dictionary for folders with data and corresponding data type
            # for. ex. {"nii": "MRI"}
            "rec_folders":{},
            # Path to template json file defining subject tsv columns
            "part_template": ~
            }
