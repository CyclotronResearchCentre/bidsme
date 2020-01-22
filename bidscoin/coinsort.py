#!/usr/bin/env python
"""
Sorts and renames NII files into local sub-direcories
/sub-xxx/[ses-xxx/]zzz[-seriename]/file.nii
/sub-xxx/[ses-xxx/]zzz[-seriename]/file.json

creates in destination directory participants.tsv with subject
information from external source
"""
import os
import logging
import time as tm
import traceback

import bids

from tools import info
import tools.tools as tools
import plugins 
import exceptions

from Modules import select


logger = logging.getLogger()
logger.name = os.path.splitext(os.path.basename(__file__))[0]
info.setup_logging(logger, "", 'INFO')


def sortsession(scan: dict,
                recording: object) -> None: 

    logger.info("Processing: sub '{}', ses '{}' ({} files)"
                .format(scan["subject"],
                        scan["session"],
                        len(recording.files)))

    outfolder = scan["out_path"]

    recording.index = -1
    while recording.loadNextFile():
        plugins.RunPlugin("RecordingEP", recording)
        serie = os.path.join(
                outfolder, 
                "{}/{}".format(recording.Module(),
                               recording.recIdentity(index=False)))
        if not os.path.isdir(serie):
            os.makedirs(serie)
        outfile = recording.copyRawFile(serie)
        plugins.RunPlugin("FileEP", outfile, recording)
    plugins.RunPlugin("SequenceEndEP", outfolder, recording)

def sortsessions(source: str, destination:str,
                 subjectid: str='', sessionid: str='',
                 recfolder: list=[''],
                 rectypes: list=[''],
                 sessions: bool=True,
                 subjects: bool=True,
                 plugin_file: str="",
                 plugin_opt: dict={}) -> None:

    # Input checking
    source = os.path.realpath(source)

    plugins.ImportPlugins(plugin_file)
    plugins.InitPlugin(source=source, 
                       destination=destination,
                       dry=False,
                       **plugin_opt)

    scan = {"subject": "", "session": "", "in_path": "", "out_path": ""}

    if subjects:
        folders = tools.lsdirs(source, subjectid + '*')
    else:
        folders = [source]

    for f in folders:
        if subjects:
            scan["subject"] = os.path.basename(f)[len(subjectid):]
        else:
            scan["subject"] = ""
        plugins.RunPlugin("SubjectEP", scan)

        # get name of subject from folder name
        if sessions:
            sfolders = tools.lsdirs(f, sessionid + '*')
        else:
            sfolders = [f]

        for s in sfolders:
            scan["in_path"] = s
            if sessions:
                scan["session"] = os.path.basename(s)
            else:
                scan["session"] = ""
            plugins.RunPlugin("SessionEP", scan)

            if not scan["subject"].startswith("sub-"):
                scan["subject"] = "sub-" + scan["subject"]
            if not scan["session"].startswith("ses-"):
                scan["session"] = "ses-" + scan["session"]

            scan["out_path"] = os.path.join(destination, 
                                            scan["subject"], 
                                            scan["session"])
            os.makedirs(scan["out_path"], exist_ok=True)
            if scan["session"] == "ses-":
                scan["session"] = ""

            logger.info("Scanning subject {}/{} in {}"
                        .format(scan["subject"],
                                scan["session"], 
                                s))

            if not recfolder:
                recfolder = [""]
                rectypes = [""]

            if not rectypes:
                rectypes = [""] * len(recfolder)

            if len(recfolder) != len(rectypes):
                logger.critical("Size of list of data folders mismach "
                                "size of list of types")
                raise IndexError("List of types size")

            for rec_f, rec_t in zip(recfolder, rectypes):
                path = os.path.join(s, rec_f)
                if not os.path.isdir(path):
                    logger.warning("Sub: '{}', Ses: '{}' : '{}' don't exists "
                                   "or not a folder"
                                   .format(scan["subject"],
                                           scan["session"],
                                           path))
                    continue
                cls = select(path, rec_t)
                if cls is None:
                    logger.warning("Unable to identify data in folder {}"
                                   .format(path))
                    continue
                recording = cls(rec_path=path)
                if not recording or len(recording.files) == 0:
                    logger.warning("unable to load data in folder {}"
                                   .format(path))
                recording.setSubId(scan["subject"])
                recording.setSesId(scan["session"])
                plugins.RunPlugin("SequenceEP", recording)

                sortsession(scan, 
                            recording)
            plugins.RunPlugin("SessionEndEP", scan)

    plugins.RunPlugin("FinaliseEP")

if __name__ == "__main__":
    # Parse the input arguments and run the sortsessions(args)
    import argparse
    import textwrap

    class appPluginOpt(argparse.Action):
        def __call__(self, parser, args, values, option_string=None):
            if getattr(args, self.dest) is None:
                setattr(args, self.dest, dict())
            for v in values:
                key, value = v.split("=", maxsplit=1)
                getattr(args, self.dest)[key] = value

    class CustomFormatter(argparse.ArgumentDefaultsHelpFormatter, 
                          argparse.RawDescriptionHelpFormatter):
        pass

    parser = argparse.ArgumentParser(formatter_class=CustomFormatter,
                                     description=textwrap.dedent(__doc__),
                                     epilog='examples:\n')
    parser.add_argument('source',
                        help='The name of the root folder containing ' 
                        'the recording file source/[sub/][ses/]<type>'),
    parser.add_argument('destination',
                        help='The name of the folder where sotred ' 
                        'files will be placed'),
    parser.add_argument('-i','--subjectid', 
                        help='The prefix string for recursive searching '
                        'in niisource/subject subfolders (e.g. "sub-")',
                        default=''),
    parser.add_argument('-j','--sessionid', 
                        help='The prefix string for recursive searching '
                        'in niisource/subject/session '
                        'subfolders (e.g. "ses-")',
                        default=''),
    parser.add_argument('-r', '--recfolder',
                        help='Comma-separated list of folders with all '
                        'recording files files',
                        default='')
    parser.add_argument('-t', '--rectype',
                        help='Comma-separated list of types associated '
                        'with recfolder folders. Must have same dimentions.',
                        default='')
    parser.add_argument('--no-session',
                        help='Dataset do not contains session folders',
                        action='store_true')
    parser.add_argument('--no-subject',
                        help='Dataset do not contains subject folders',
                        action='store_true')
    parser.add_argument('-p', '--plugin',
                        help="Path to a plugin file",
                        default="")
    parser.add_argument('-o',
                        metavar="OptName=OptValue",
                        dest="plugin_opt",
                        help="Options passed to plugin in form "
                        "-o OptName=OptValue, several options can be passed",
                        action=appPluginOpt,
                        default={},
                        nargs="+"
                        )

    args = parser.parse_args()

    code = 0
    logger.info("")
    logger.info('-------------- START coinsort --------------')
    logger.info('bidscoin ver {}'.format(info.version()))
    logger.info('bids ver {}'.format(info.bidsversion()))

    try: 
        sortsessions(source=args.source,
                     destination=args.destination,
                     subjectid=args.subjectid,
                     sessionid=args.sessionid,
                     recfolder=args.recfolder.split(','),
                     rectypes=args.rectype.split(','),
                     sessions=not args.no_session,
                     subjects=not args.no_subject,
                     plugin_file=args.plugin,
                     plugin_opt=args.plugin_opt)
    except Exception as err:
        if isinstance(err, exceptions.CoinException):
            code = err.base + err.code
        exc_type, exc_value, exc_traceback = os.sys.exc_info()
        tr = traceback.extract_tb(exc_traceback)
        for l in tr:
            logger.error("{}({}) in {}: "
                         .format(l[0], l[1], l[2]))
        logger.error("{}({}): {}".format(exc_type.__name__, code, exc_value))
        logger.info("Command: {}".format(os.sys.argv))
    logger.info('-------------- FINISHED! -------------------')
    info.reporterrors(logger)
    logger.info("Took {} seconds".format(tm.process_time()))
    logger.info('--------------------------------------------')
    os.sys.exit(code)
