#!/usr/bin/env python
"""
Sorts and / or renames DICOM files into local subdirectories with a (3-digit) SeriesNumber-SeriesDescription directory name (i.e. following the same listing as on the scanner console)
"""

import os
import re
import warnings
try:
    from bidscoin import bids
except ImportError:
    import bids         # This should work if bidscoin was not pip-installed


def sortsession(sessionfolder, pattern, rename, nosort):
    """
    Sorts dicomfiles into (3-digit) SeriesNumber-SeriesDescription subfolders (e.g. '003-T1MPRAGE')

    :param str sessionfolder:   The name of the folder that contains the dicom files
    :param str pattern:         The regular expression pattern used in re.match(pattern, dicomfile) to select the dicom files
    :param bool rename:         Boolean to rename the DICOM files to a PatientName_SeriesNumber_SeriesDescription_AcquisitionNumber_InstanceNumber scheme
    :param bool nosort:         Boolean to skip sorting of DICOM files into SeriesNumber-SeriesDescription directories (useful in combination with -r for renaming only)
    :return:                    Nothing
    :rtype: NoneType
    """

    # Input checking
    sessionfolder = os.path.abspath(os.path.expanduser(sessionfolder))
    seriesdirs    = []
    print('>> processing: ' + sessionfolder)

    # Map all dicomfiles and move them to series folders
    for dicomfile in [os.path.join(sessionfolder,dcmfile) for dcmfile in os.listdir(sessionfolder) if re.match(pattern, dcmfile)]:

        # Extract the SeriesDescription and SeriesNumber from the dicomfield
        seriesnr    = bids.get_dicomfield('SeriesNumber', dicomfile)
        seriesdescr = bids.get_dicomfield('SeriesDescription', dicomfile)
        if not seriesdescr:
            seriesdescr = bids.get_dicomfield('ProtocolName', dicomfile)
            if not seriesdescr:
                seriesdescr = 'unknown_protocol'
                warnings.warn('No SeriesDecription or ProtocolName found for: ' + dicomfile)
        if rename:
            acquisitionnr = bids.get_dicomfield('AcquisitionNumber', dicomfile)
            instancenr    = bids.get_dicomfield('InstanceNumber', dicomfile)
            if not instancenr:
                instancenr = bids.get_dicomfield('ImageNumber', dicomfile)          # This Attribute was named Image Number in earlier versions of this Standard
            patientname    = bids.get_dicomfield('PatientName', dicomfile)
            if not patientname:
                patientname = bids.get_dicomfield('PatientsName', dicomfile)        # This Attribute was/is sometimes called PatientsName?
            ext = os.path.splitext(dicomfile)[1]

        # Move and/or rename the dicomfile in(to) the (series sub)folder
        if rename:
            filename = '{patientname}_{seriesnr:03d}_{seriesdescr}_{acquisitionnr:05d}_{instancenr:05d}{ext}'.format(patientname=patientname, seriesnr=seriesnr, seriesdescr=seriesdescr, acquisitionnr=acquisitionnr, instancenr=instancenr, ext=ext)
        else:
            filename = os.path.basename(dicomfile)
        if nosort:
            pathname = sessionfolder
        else:
            # Create the series subfolder
            seriesdir = '{:03d}-{}'.format(seriesnr, seriesdescr)
            if seriesdir not in seriesdirs:  # We have a new series
                if not os.path.isdir(os.path.join(sessionfolder, seriesdir)):
                    print('  Creating:  ' + os.path.join(sessionfolder, seriesdir))
                    os.makedirs(os.path.join(sessionfolder, seriesdir))
                seriesdirs.append(seriesdir)
            pathname = os.path.join(sessionfolder, seriesdir)
        os.rename(dicomfile, os.path.join(pathname, filename))


def sortsessions(rawfolder, subjectid='', sessionid='', pattern='.*\.(IMA|dcm)$', rename=False, nosort=False):
    """

    :param rawfolder:   The root folder containing the source [sub/][ses/]dicomfiles
    :param subjectid:   The prefix of the sub folders in rawfolder
    :param sessionid:   The prefix of the ses folders in sub folder
    :param pattern:     The regular expression pattern used in re.match() to select the dicom files
    :param bool rename: Boolean to rename the DICOM files to a PatientName_SeriesNumber_SeriesDescription_AcquisitionNumber_InstanceNumber scheme
    :param bool nosort: Boolean to skip sorting of DICOM files into SeriesNumber-SeriesDescription directories (useful in combination with -r for renaming only)
    :return:            Nothing
    :rtype: NoneType
    """

    if subjectid:
        for subfolder in bids.lsdirs(rawfolder, subjectid + '*'):
            if sessionid:
                for sesfolder in bids.lsdirs(subfolder, sessionid + '*'):
                    sortsession(sesfolder, pattern, rename, nosort)
            else:
                sortsession(subfolder, pattern, rename, nosort)
    else:
        sortsession(rawfolder, pattern, rename, nosort)


# Shell usage
if __name__ == "__main__":

    # Parse the input arguments and run the sortsessions(args)
    import argparse
    import textwrap

    class CustomFormatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter):
        pass

    parser = argparse.ArgumentParser(formatter_class=CustomFormatter,
                                     description=textwrap.dedent(__doc__),
                                     epilog='examples:\n' 
                                            '  dicomsort.py /project/3022026.01/raw\n' 
                                            '  dicomsort.py /project/3022026.01/raw --subjectid sub\n' 
                                            '  dicomsort.py /project/3022026.01/raw --subjectid sub --sessionid ses\n ')
    parser.add_argument('rawfolder',      help='The root folder containing the rawfolder/[sub/][ses/]dicomfiles')
    parser.add_argument('--subjectid',    help='The prefix of the subject folders in rawfolder to search in (e.g. "sub")')
    parser.add_argument('--sessionid',    help='The prefix of the session folders in the subject folder to search in (e.g. "ses")')
    parser.add_argument('-r','--rename',  help='Flag to rename the DICOM files to a PatientName_SeriesNumber_SeriesDescription_AcquisitionNumber_InstanceNumber scheme', action='store_true')
    parser.add_argument('-n','--nosort',  help='Flag to skip sorting of DICOM files into SeriesNumber-SeriesDescription directories (useful in combination with -r for renaming only)', action='store_true')
    parser.add_argument('-p','--pattern', help='The regular expression pattern used in re.match(pattern, dicomfile) to select the dicom files', default='.*\.(IMA|dcm)$')
    args = parser.parse_args()

    sortsessions(rawfolder=args.rawfolder, subjectid=args.subjectid, sessionid=args.sessionid, pattern=args.pattern, rename=args.rename, nosort=args.nosort)
