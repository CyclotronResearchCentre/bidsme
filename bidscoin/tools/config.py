import argparse
import sys

from tools import info
from tools.yaml import yaml
from tools.config_default import config


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
        try:
            for v in values:
                key, value = v.split("=", maxsplit=1)
                getattr(args, self.dest)[key] = value
        except Exception:
            raise ValueError("Failed parce {}"
                             .format(values))


class __CustomFormatter(argparse.ArgumentDefaultsHelpFormatter,
                        argparse.RawDescriptionHelpFormatter):
    pass


def parseArgs(argv: list) -> (str, argparse.ArgumentParser):
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
    subparsers = parser.add_subparsers(
            title="subcommands",
            metavar="",
            dest="cmd"
            )

    sub_parsers = {
            "prepare": subparsers.add_parser(
                name="prepare",
                description="Preparation of dataset for bidsification",
                help="Preparation of dataset for bidsification",
                formatter_class=__CustomFormatter,
                add_help=False
                ),
            "bidsify": subparsers.add_parser(
                name="bidsify",
                description="Bidsification of dataset",
                help="Bidsification of dataset",
                formatter_class=__CustomFormatter,
                add_help=False
                ),
            "map": subparsers.add_parser(
                name="map",
                description="Create/Adapt bidsmap.yaml file",
                help="Create/Adapt bidsmap.yaml file",
                formatter_class=__CustomFormatter,
                add_help=False
                )
            }

    prog = parser.prog
    ###################
    # Loadng cfg file
    ###################
    # parcing known arguments and getting command
    args = parser.parse_known_args(argv)
    if args[0].cmd is None:
        parser.print_help()
        sys.exit(2)
    # loading configuration proper
    if args[0].configuration is not None:
        loadConfig(args[0].configuration)

    cmd = args[0].cmd
    parser = sub_parsers[cmd]
    setSubParser(parser, cmd)
    if cmd == "prepare":
        setPrepare(parser)
    elif cmd == "bidsify":
        setBidsify(parser)
    elif cmd == "map":
        setMap(parser)

    gr_help = parser.add_argument_group(
            title="Help",
            )
    gr_help.add_argument(
            "-h", "--help",
            help="show this help message and exit",
            action="help"
            )
    args = parser.parse_args(args[1], args[0])
    return prog, args


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
        yaml_map = yaml.load(f)
    for key, val in config.items():
        if key in yaml_map:
            for key2 in val:
                if key2 in yaml_map[key]:
                    val[key2] = yaml_map[key][key2]


def setSubParser(parser, cmd):
    parser.add_argument(
            "source",
            help="Path to the source dataset"
            )
    parser.add_argument(
            "destination",
            help="Path to the destination dataset"
            )

    gr_plugin = parser.add_argument_group(
            title="plugin arguments",
            description="Options related to plugins"
            )
    gr_plugin.add_argument(
            "--plugin",
            help="Path to the plugin file"
            )
    gr_plugin.add_argument(
            "-o",
            metavar="Name=Value",
            dest="plugin_opt",
            help="Options passed to plugin"
            ", several options can be passed",
            action=__appPluginOpt,
            default={},
            nargs="+"
            )

    gr_selection = parser.add_argument_group(
            title="selection arguments",
            description="Option for selecting subjects and sessions from "
            "source dataset to process.")
    gr_selection.add_argument(
            "--participants",
            help="Space-separated list of subjects to process, as "
            "defined in source folder (i.e. before affecting by plugin)",
            metavar="ID",
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

    parser.set_defaults(
            plugin=config["plugins"][cmd]["path"],
            plugin_opt=config["plugins"][cmd]["options"],
            skip_in_tsv=config["selection"]["skip_tsv"],
            skip_existing=config["selection"]["skip_existing"],
            skip_existing_sessions=config["selection"]["skip_session"]
            )


def setPrepare(parser):
    gr_template = parser.add_argument_group(
            title="template commands",
            description="Files used for templates")
    gr_template.add_argument('--part-template',
                             help='Path to the template used for '
                             'participants.tsv',
                             metavar="TEMPLATE")
    gr_prefix = parser.add_argument_group(
            title="prefixes commands",
            description="Prefixes for identifying subject "
            "and session filders")
    gr_prefix.add_argument('--sub-prefix',
                           help='The prefix string for recursive searching '
                           'in niisource/subject subfolders (e.g. "sub-")',
                           metavar="PREFIX"
                           ),
    gr_prefix.add_argument('--ses-prefix',
                           help='The prefix string for recursive searching '
                           'in niisource/subject/session '
                           'subfolders (e.g. "ses-")',
                           metavar="PREFIX"
                           ),
    gr_prefix.add_argument('--no-subject',
                           help='Dataset do not contains subject folders',
                           action='store_true')
    gr_prefix.add_argument('--no-session',
                           help='Dataset do not contains session folders',
                           action='store_true')

    gr_data = parser.add_argument_group(
            title="data identification parameters",
            description="Option for succesful identification of "
            "folders containing data files.")
    gr_data.add_argument('-r', '--recfolder',
                         metavar="folder=type",
                         help="List of folders containing data files "
                         "in form -r 'nii=MRI'",
                         action=__appPluginOpt,
                         default={},
                         nargs="+")
    # Updating defaults
    cfg = config["prepare"]
    parser.set_defaults(
            sub_prefix=cfg["sub_prefix"],
            ses_prefix=cfg["ses_prefix"],
            no_subject=cfg["no_subject"],
            no_session=cfg["no_session"],
            recfolder=cfg["rec_folders"],
            part_template=cfg["part_template"])


def setBidsify(parser):
    gr_maps = parser.add_argument_group(
            title="map parameters"
            )
    gr_maps.add_argument('-b', '--bidsmap',
                         help='The bidsmap YAML-file with the study '
                         'heuristics.'
                         )
    parser.set_defaults(
            bidsmap=config["maps"]["map"])


def setMap(parser):
    gr_maps = parser.add_argument_group(
            title="map parameters"
            )
    gr_maps.add_argument('-b', '--bidsmap',
                         help='The bidsmap YAML-file with the study '
                         'heuristics.'
                         )
    gr_maps.add_argument('-t', '--template',
                         help='The bidsmap template with the default '
                         'heuristics')
    parser.set_defaults(
            bidsmap=config["maps"]["map"],
            template=config["maps"]["template"])
