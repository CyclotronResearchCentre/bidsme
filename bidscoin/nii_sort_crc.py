#!/usr/bin/env python
"""
Sorts and renames NII files into local sub-direcories
/sub-xxx/[ses-xxx/]zzz[-seriename]/file.nii
/sub-xxx/[ses-xxx/]zzz[-seriename]/file.json

creates in destination directory participants.tsv with subject
information from external source
"""

"""
TODO:
    possibility to not have sessions and/or subjects 
        (use PatientID and StudyID)
    plugins to rename subject and session
"""


import os
import re
import warnings
import json
import shutil
import importlib.util

import bids
import tools.plugins as plugins
import tools.exceptions as exceptions


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


plugins.entry_points = {
        "SubjectEP" : SubjectEPerror,
        "SessionEP" : SessionEPerror
        }

def sortsession(destination: str, 
                sub: str, ses: str,
                niifiles: list) -> None: 

    if len(niifiles) == 0:
        print('>> No files to process')
        return
    print('>> Processing: sub-{}/ses-{} ({} files)'
          .format(sub,ses,len(niifiles)))
    outfolder = os.path.join(destination, 
                             "sub-" + sub,
                             "ses-" + ses)
    if not os.path.isdir(outfolder):
        os.makedirs(outfolder)

    for niifile in niifiles:
        json_file = niifile[:-len(".nii")] + ".json"
        with open(json_file, "r") as f:
            meta = json.load(f)["acqpar"][0]

        seriesnr = meta["SeriesNumber"]
        seriesdescr = meta["SeriesDescription"].strip()
        acqnumber = meta["AcquisitionNumber"]
        instnumber = meta["InstanceNumber"]

        if not seriesnr:
            warnings.warn('No SeriesNumber found, skipping: {}'
                          .format(niifile))
            continue
        if not seriesdescr:
            seriesdescr = meta['ProtocolName'].strip()
            if not seriesdescr:
                seriesdescr = 'unknown_protocol'
                warnings.warn('No SeriesDecription or '
                              'ProtocolName found for: {}'
                              .format(niifile))
        serie = os.path.join(outfolder, "{}-{}".format(seriesnr, seriesdescr))
        if not os.path.isdir(serie):
            os.mkdir(serie)
        shutil.copy(niifile, serie)
        shutil.copy(json_file, serie)

class CScan():
    def __init__(self):
        self.subject = ""
        self.session = ""
        self.in_path = ""
        self.out_path = ""

def sortsessions(session: str, destination:str,
                 subjectid: str='', sessionid: str='',
                 niifolder: str='nii',
                 plugin_file: str="",
                 plugin_opt: dict={}) -> None:

    # Input checking
    session = os.path.abspath(os.path.expanduser(session))

    plugins.ImportPlugins(plugin_file)
    scan = CScan()
    scan.in_path = session
    scan.out_path = destination

    # Define the sessionfolder, collect all DICOM files and run sortsession()
    folders = bids.lsdirs(session, subjectid + '*')
    for f in folders:
        scan.subject = os.path.basename(f)[len(subjectid):]
        plugins.RunPlugin("SubjectEP", [scan], opt=plugin_opt)
        # get name of subject from folder name
        sfolders = bids.lsdirs(f, sessionid + '*')
        for s in sfolders:
            scan.session = os.path.basename(s)
            if plugins.RunPlugin("SessionEP", [scan], opt=plugin_opt) is None:
                scan.session = os.path.basename(scan.session)[len(sessionid):]

            path = os.path.join(s, niifolder)
            if not os.path.isdir(path):
                warnings.warn("Sub: {}, Ses:{}: {} don't exists "
                              "or not a folder"
                              .format(scan.subject,scan.session,path))
                continue
            niifiles = [os.path.join(path, niifile) 
                        for niifile in os.listdir(path)
                        if niifile.endswith(".nii")]
            sortsession(destination,
                        scan.subject, 
                        scan.session, 
                        niifiles)


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
    parser.add_argument('niisource',
                        help='The name of the root folder containing ' 
                        'the dicomsource/[sub/][ses/]nii'),
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
    parser.add_argument('-n', '--niifolder',
                        help='The name of folder containing all nii files',
                        default='nii')
    parser.add_argument('-p', '--plugin',
                        help="Path to a plugin file",
                        default="")
    parser.add_argument('-o',
                        metavar="OptName=OptValue",
                        dest="plugin_opt",
                        help="Options passed to plugin in form "
                        "-o OptName=OptValue, several options can be passed",
                        action=appPluginOpt,
                        nargs="+"
                        )
    args = parser.parse_args()

    sortsessions(session=args.niisource,
                 destination=args.destination,
                 subjectid=args.subjectid,
                 sessionid=args.sessionid,
                 niifolder=args.niifolder,
                 plugin_file=args.plugin,
                 plugin_opt=args.plugin_opt)
