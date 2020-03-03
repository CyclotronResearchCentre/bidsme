import os
import logging

from tools.yaml import yaml
from tools.config_default import config

logger = logging.getLogger(__name__)

def exportConfig(filename: str) -> None:
    with open(filename, "w") as f:
        yaml.dump(config, f)

def loadConfig(filename: str) -> None:
    with open(filename, "r") as f:
        try:
            yaml_map = yaml.load(f)
        except Exception as e:
            err = sys.exc_info()
            logger.error("Failed to load configuration from {}"
                         .format(filename))
            logger.error("{}: {}".format(err[0], err[1]))
            raise
    for key, val in config.items():
        if key in yaml_map:
            for key2 in val:
                if key2 in yaml_map[key]:
                    val[key2] = yaml_map[key][key2]

def mergeCLI(args, stage) -> None:
    if stage == "sorting":
        if args.part_template:
            config["preparation"]["part_template"] = args.part_template
        if args.subjectid:
            config["preparation"]["sub_prefix"] = args.subjectid
        if args.sessionid:
            config["preparation"]["ses_prefix"] = args.sessionid
        folders = args.recfolder.split(",")
        if not args.rectypes:
            types = [""] * len(folders)
        else:
            types = args.rectypes.split(",")
        if len(folders) != len(types):
            logger.critical("Lenght of rec folders mismatch lenght of given types")
            raise ValueError("Rec folders mismatch list of types")
        if folders[0]:
            config["preparation"]["rec_folders"] = {key, val 
                                                    for key, val 
                                                    in zip(folders, types)}
        if args.no-session:
            config["preparation"]["no_session"] = True
        if args.no-subject:
            config["preparation"]["no_subject"] = True
        if args.plugin:
            config["plugins"]["preparation"]["path"] = args.plugin
            config["plugins"]["preparation"]["options"] = args.appPluginOpt
        elif args.appPluginOpt:
            config["plugins"]["preparation"]["options"] = args.appPluginOpt

def validateConfig() -> None:
    passed = True
    # checking maps





    tmp = config["preparation"]["part_template"]
    if tmp:
        if not os.path.isfile(tmp):
            logger.critical("Subject tsv template {} not found"
                            .format(tmp))
            passed = False
