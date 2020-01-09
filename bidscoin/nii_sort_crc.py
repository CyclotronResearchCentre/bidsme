#!/usr/bin/env python
"""
Sorts and renames NII files into local sub-direcories
/sub-xxx/[ses-xxx/]zzz[-seriename]/file.nii
/sub-xxx/[ses-xxx/]zzz[-seriename]/file.json

creates in destination directory participants.tsv with subject
information from external source
"""
import os
import warnings
import logging

import bids

from tools import info
import tools.tools as tools
import tools.plugins as plugins
import tools.exceptions as exceptions

from Modules.MRI.selector import select as MRI_select


logger = logging.getLogger()
logger.name = os.path.splitext(os.path.basename(__file__))[0]
info.setup_logging(logger, "", 'INFO')


class SubjectEPerror(exceptions.PluginError):
    """
    Raises if error occured in SubjectEP plugin
    """
    code = 110


class SessionEPerror(exceptions.PluginError):
    """
    Raises if error occured in SubjectEP plugin
    """
    code = 120

class RecordingEPerror(exceptions.PluginError):
    """
    Raises if error occured in RecordingEP plugin
    """
    code = 130

class FileEPerror(exceptions.PluginError):
    """
    Raises if error occured in FileEP plugin
    """
    code = 140

plugins.entry_points = {
        "InitEP" : exceptions.PluginError,
        "SubjectEP" : SubjectEPerror,
        "SessionEP" : SessionEPerror,
        "RecordingEP" : RecordingEPerror,
        "FileEP" : FileEPerror
        }


def sortsession(destination: str, 
                scan: dict,
                recording: object) -> None: 

    logger.info("Processing: sub '{}', ses '{}' ({} files)"
                .format(scan["subject"],
                        scan["session"],
                        len(recording.files)))

    outfolder = os.path.join(destination, 
                             bids.add_prefix("sub-",scan["subject"]),
                             bids.add_prefix("ses-",scan["session"]))

    if not os.path.isdir(outfolder):
        os.makedirs(outfolder)

    recording.index = -1
    while recording.loadNextFile():
        seriesnr = recording.get_rec_no()
        if seriesnr is None:
            seriesnr = 0
        seriesdescr = recording.get_rec_id()

        serie = os.path.join(outfolder, 
                "{}/{:03}-{}".format(recording.Module,
                                     seriesnr, seriesdescr))
        plugins.RunPlugin("FileEP", scan, serie, recording)
        if not os.path.isdir(serie):
            os.makedirs(serie)
        recording.copy_file(serie)


def sortsessions(source: str, destination:str,
                 subjectid: str='', sessionid: str='',
                 recfolder: list=[''],
                 rectypes: list=[''],
                 sessions: bool=True,
                 plugin_file: str="",
                 plugin_opt: dict={}) -> None:

    # Input checking
    source = os.path.realpath(source)

    plugins.ImportPlugins(plugin_file)
    plugin_opt["source"] = source
    plugin_opt["destination"] = destination
    plugins.InitPlugin(plugin_opt)

    scan = {"subject": "", "session": "", "path": ""}

    folders = tools.lsdirs(source, subjectid + '*')

    for f in folders:
        scan["subject"] = os.path.basename(f)[len(subjectid):]
        plugins.RunPlugin("SubjectEP", scan)

        # get name of subject from folder name
        if sessions:
            sfolders = tools.lsdirs(f, sessionid + '*')
        else:
            sfolders = [f]

        for s in sfolders:
            if sessions:
                scan["session"] = os.path.basename(s)
            else:
                scan["session"] = ''
            plugins.RunPlugin("SessionEP", scan)
            logger.info("Scanning subject {}/{} in {}"
                        .format(scan["subject"],
                                scan["session"], 
                                s))

            scan["path"] = os.path.join(destination, 
                                        bids.add_prefix("sub-",
                                                        scan["subject"]),
                                        bids.add_prefix("ses-",
                                                        scan["session"]))

            for rec_f, rec_t in zip(recfolder, rectypes):
                path = os.path.join(s, rec_f)
                if not os.path.isdir(path):
                    logger.warning("Sub: '{}', Ses: '{}' : '{}' don't exists "
                                   "or not a folder"
                                   .format(scan["subject"],
                                           scan["session"],
                                           path))
                    continue
                cls = MRI_select(path, rec_t)
                if cls is None:
                    logger.warning("Unable to identify data in folder {}"
                                  .format(path))
                    continue
                recording = cls(rec_path=path)
                if not recording or len(recording.files) == 0:
                    logger.warning("unable to load data in folder {}"
                                  .format(path))

                plugins.RunPlugin("RecordingEP", scan, recording)
                sortsession(destination,
                            scan, 
                            recording)


# Shell usage
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
                        help='Dataset do not contains session',
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

    sortsessions(source=args.source,
                 destination=args.destination,
                 subjectid=args.subjectid,
                 sessionid=args.sessionid,
                 recfolder=args.recfolder.split(','),
                 rectypes=args.rectype.split(','),
                 sessions=not args.no_session,
                 plugin_file=args.plugin,
                 plugin_opt=args.plugin_opt)
