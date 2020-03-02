#!/usr/bin/env python
"""
Sorts and data files into local sub-direcories
destination/sub-xxx/ses-xxx/zzz-seriename/<data-file>

Plugins allow to modify subjects and session names
and preform various operations on data files.
"""
import os
import logging
import time
import traceback
import argparse
import textwrap
import glob

from tools import info
import tools.tools as tools
import plugins 
import exceptions

from Modules import select
from bids import BidsSession


logger = logging.getLogger()
logger.name = os.path.splitext(os.path.basename(__file__))[0]
info.setup_logging(logger, 'INFO')


def sortsession(outfolder: str,
                recording: object) -> None: 

    logger.info("Processing: sub '{}', ses '{}' ({} files)"
                .format(recording.subId(),
                        recording.sesId(),
                        len(recording.files)))

    os.makedirs(outfolder, exist_ok=True)
    recording.index = -1
    while recording.loadNextFile():
        plugins.RunPlugin("RecordingEP", recording)
        recording.getBidsSession().registerFields(True)
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
                 part_template: str=None,
                 recfolder: list=[''],
                 rectypes: list=[''],
                 sessions: bool=True,
                 subjects: bool=True,
                 plugin_file: str="",
                 plugin_opt: dict={}) -> None:

    # Input checking
    source = os.path.abspath(source)

    plugins.ImportPlugins(plugin_file)
    plugins.InitPlugin(source=source, 
                       destination=destination,
                       dry=False,
                       **plugin_opt)

    if subjects:
        folders = tools.lsdirs(source, subjectid + '*')
    else:
        folders = [source]

    BidsSession.loadSubjectFields(part_template)
    ####################
    ## Subject loop
    ####################
    for f in folders:
        scan = BidsSession()
        scan.in_path = f
        if subjects:
            scan.subject = os.path.basename(f)[len(subjectid):]
        plugins.RunPlugin("SubjectEP", scan)

        # get name of subject from folder name
        if sessions:
            sfolders = tools.lsdirs(f, sessionid + '*')
        else:
            sfolders = [f]

        ####################
        ## Session loop
        ####################
        for s in sfolders:
            scan.in_path = s
            if sessions:
                scan.unlock_session()
                scan.session = os.path.basename(s)[len(sessionid):]
            plugins.RunPlugin("SessionEP", scan)
            scan.lock()

            logger.info("Scanning subject {}/{} in {}"
                        .format(scan.subject,
                                scan.session, 
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
                paths = [f for f in glob.glob(os.path.join(s, rec_f) + "/")]
                for path in paths:
                    if not os.path.isdir(path):
                        logger.warning("Sub: '{}', Ses: '{}': "
                                       "'{}' don't exists "
                                       "or not a folder"
                                       .format(scan.subject,
                                               scan.session,
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
                    recording.setBidsSession(scan)
                    plugins.RunPlugin("SequenceEP", recording)
                    scan = recording.getBidsSession()
                    out_path = os.path.join(destination, 
                                            scan.getPath(True))
                    sortsession(out_path, recording)
            # End of session
            plugins.RunPlugin("SessionEndEP", scan)
        # End of subject
        plugins.RunPlugin("SubjectEndEP", scan)
    BidsSession.exportParticipants(destination)

    plugins.RunPlugin("FinaliseEP")


if __name__ == "__main__":
    # Parse the input arguments and run the sortsessions(args)
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
    parser.add_argument('--part-template',
                        help='Path to the template used for participants.tsv')
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

    # checking paths
    if not os.path.isdir(args.source):
        logger.critical("Source directory {} don't exists"
                        .format(args.source))
        raise NotADirectoryError(args.source)
    if not os.path.isdir(args.destination):
        logger.critical("Destination directory {} don't exists"
                        .format(args.destination))
        raise NotADirectoryError(args.destination)
    if args.part_template is not None and \
            not os.path.isfile(args.part_template):
        logger.critical("Participants.tsv template not found at {}"
                        .format(args.part_template))
        raise FileNotFoundError(args.part_template)

    info.addFileLogger(logger, os.path.join(args.destination, "log"))

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
                     part_template=args.part_template,
                     recfolder=args.recfolder.split(','),
                     rectypes=args.rectype.split(','),
                     sessions=not args.no_session,
                     subjects=not args.no_subject,
                     plugin_file=args.plugin,
                     plugin_opt=args.plugin_opt)
    except Exception as err:
        if isinstance(err, exceptions.CoinException):
            code = err.base + err.code
        else:
            code = 1
        exc_type, exc_value, exc_traceback = os.sys.exc_info()
        tr = traceback.extract_tb(exc_traceback)
        for l in tr:
            logger.error("{}({}) in {}: "
                         .format(l[0], l[1], l[2]))
        logger.error("{}:{}: {}".format(code, exc_type.__name__, exc_value))
        logger.info("Command: {}".format(os.sys.argv))

    logger.info('-------------- FINISHED! -------------------')
    errors = info.reporterrors(logger)
    logger.info("Took {} seconds".format(time.process_time()))
    logger.info('--------------------------------------------')
    if code == 0 and errors > 0:
        logger.warning("Several errors detected but exit code is 0")
        code = 1
    os.sys.exit(code)
