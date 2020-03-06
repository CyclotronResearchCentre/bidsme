import argparse
import sys
import logging

from tools import info
from tools.yaml import yaml
from tools.config_default import config

logger = logging.getLogger(__name__)

__generalDescription = "Generic tool for bidsification of dataset"

__sortingDescription = """Sorts and data files into local sub-direcories
destination/sub-xxx/ses-xxx/zzz-seriename/<data-file>

Plugins allow to modify subjects and session names
and preform various operations on data files.
"""


class __appPluginOpt(argparse.Action):
    """
    Parces a set of `key=value` options into a 
    dictionary
    """
    def __call__(self, parser, args, values, option_string=None):
        if getattr(args, self.dest) is None:
            setattr(args, self.dest, dict())
        for v in values:
            key, value = v.split("=", maxsplit=1)
            getattr(args, self.dest)[key] = value


class __CustomFormatter(argparse.ArgumentDefaultsHelpFormatter, 
                        argparse.RawDescriptionHelpFormatter):
    pass


def parseArgs(argv: list) -> argparse.ArgumentParser:
    """
    Parses command-line arguments and returns resulting
    argparse.ArgumentParser object

    Parameters
    ----------
    argv: list
        list of cli parameters excluding programm name,
        typically sys.argv[1:]

    Returns
    -------
    argparse.ArgumentParser
    """

    parser = argparse.ArgumentParser(
            formatter_class=__CustomFormatter,
            description=__generalDescription,
            )
    parser.add_argument(
            "--dry-run",
            help="Run in dry mode, i.e. without writting anything "
            "on the disk",
            action="store_true"
            )
    parser.add_argument(
            '-c', '--configuration',
            metavar="conf.yaml",
            help="Path to the configuration file"
            )
    parser.add_argument(
            '-v', '--version',
            help="Show version and exit",
            action="version",
            version="%(prog)s: {}\nBIDS: {}".format(info.version(),
                                                    info.bidsversion())
            )
    common_parser = commonArgs()
    source_parser = argparse.ArgumentParser(add_help=False)
    source_parser.add_argument(
            "source",
            help="Path to the source dataset to be treated"
            )
    source_parser.add_argument(
            "destination",
            help="Path to the destination dataset"
            )

    subparsers = parser.add_subparsers(
            title="subcommands",
            metavar="",
            dest="cmd"
            )

    sub_prep = subparsers.add_parser(
            name="prepare", 
            description="Preparation of dataset for bidsification",
            help="Preparation of dataset for bidsification",
            formatter_class=__CustomFormatter,
            parents=[source_parser, common_parser])
    sub_bids = subparsers.add_parser(
            name="bidsify", 
            description="Bidsification of dataset",
            help="Bidsification of dataset",
            formatter_class=__CustomFormatter,
            parents=[source_parser, common_parser])
    sub_map = subparsers.add_parser(
            name="map", 
            description="Create/Adapt bidsmap.yaml file",
            help="Create/Adapt bidsmap.yaml file",
            formatter_class=__CustomFormatter,
            parents=[source_parser, common_parser])

    ###################
    ## Loadng cfg file
    ###################
    # args = parser.parse_known_args(argv)
    #################
    ## Preparation
    #################
    sub_prep.add_argument('--part-template',
                          help='Path to the template used for '
                          'participants.tsv')
    gr_prefix = sub_prep.add_argument_group(
            title="prefixes commands:",
            description="Prefixes for identifying subject "
            "and session filders")
    gr_prefix.add_argument('--sub-prefix',
                           help='The prefix string for recursive searching '
                           'in niisource/subject subfolders (e.g. "sub-")',
                           default=''),
    gr_prefix.add_argument('--ses-prefix', 
                           help='The prefix string for recursive searching '
                           'in niisource/subject/session '
                           'subfolders (e.g. "ses-")',
                           default=''),
    gr_prefix.add_argument('--no-session',
                           help='Dataset do not contains session folders',
                           action='store_true')
    gr_prefix.add_argument('--no-subject',
                           help='Dataset do not contains subject folders',
                           action='store_true')

    gr_data = sub_prep.add_argument_group(
            title="data identification parameters:",
            description="Option for succesful identification of "
            "folders containing data files.")
    gr_data.add_argument('-r', '--recfolder',
                         metavar="folder=type",
                         help="List of folders containing data files "
                         "in form -r 'nii=MRI'",
                         action=__appPluginOpt,
                         default={},
                         nargs="+")

    args = parser.parse_known_args(argv)
    if args[0].cmd is None:
        parser.print_help()
        sys.exit(2)

    if args[0].configuration is not None:
        loadConfig(args[0].configuration)

    set_defaults(args[0])
    args = parser.parse_args(args[1], args[0])
    return args


def loadConfig(filename: str) -> None:
    """
    Loads config yaml file from given path
    and merges it with config_defaults

    Parameters
    ----------
    filename: str
        path to config file
    """
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


def commonArgs() -> argparse.ArgumentParser:
    """
    Returns common arguments for all commands
    """
    common_parser = argparse.ArgumentParser(
            formatter_class=__CustomFormatter,
            add_help=False)
    gr_plugin = common_parser.add_argument_group(
            title="plugin arguments",
            description="Options related to plugins"
            )
    gr_plugin.add_argument(
            "--plugin",
            help="Path to the plugin file"
            )
    gr_plugin.add_argument(
            "-o",
            metavar="OptName=OptValue",
            dest="plugin_opt",
            help="Options passed to plugin in form "
            "-o OptName=OptValue, several options can be passed",
            action=__appPluginOpt,
            default={},
            nargs="+"
            )

    gr_selection = common_parser.add_argument_group(
            title="selection arguments",
            description="Option for selecting subjects and sessions from "
            "source dataset to process.")
    gr_selection.add_argument(
            "--participants",
            help="Space-separated list of subjects to process, as "
            "defined in source folder (i.e. before affecting by plugin)",
            nargs='+'
            )
    gr_selection.add_argument(
            "--skip-in-tsv",
            help="Skip participants that exists in the participants.tsv "
            "file in destination dataset.",
            action='store_true'
            )
    gr_selection.add_argument(
            "--skip-existing",
            help="Skip participants with corresponding folders  exists "
            "in destination dataset.",
            action='store_true'
            )
    gr_selection.add_argument(
            "--skip-existing-sessions",
            help="Skip sessions that exists in destination dataset.",
            action="store_true"
            )
    return common_parser


def set_defaults(parser) -> None:
    cmd = parser.cmd
    parser.plugin=config["plugins"][cmd]["path"]
    parser.plugin_opt=config["plugins"][cmd]["options"]
    parser.participants=None
    parser.skip_in_tsv=config["selection"]["skip_tsv"]
    parser.skip_existing=config["selection"]["skip_existing"]
    parser.skip_existing_sessions=config["selection"]["skip_session"]

    if cmd == "prepare":
        parser.part_template=config["maps"]["template"]
        parser.sub_prefix=config[cmd]["sub_prefix"]
        parser.ses_prefix=config[cmd]["ses_prefix"]
        parser.no_session=config[cmd]["no_session"]
        parser.no_subject=config[cmd]["no_subject"]
        parser.recfolder=config[cmd]["rec_folders"]


