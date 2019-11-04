import os

ROW_HEIGHT = 22

ICON_FILENAME = os.path.join(os.path.dirname(os.path.realpath(__file__)), 
                             "icons", "bidscoin.ico")

MAIN_HELP_URL = "https://github.com/Donders-Institute/"\
                "bidscoin/blob/master/README.md"

HELP_URL_DEFAULT = "https://bids-specification.readthedocs.io/en/latest/"

HELP_URLS = {
    "anat": HELP_URL_DEFAULT + "/04-modality-specific-files/"
    "01-magnetic-resonance-imaging-data.html#anatomy-imaging-data",
    "beh" : HELP_URL_DEFAULT + "/04-modality-specific-files/"
    "07-behavioral-experiments.html",
    "dwi" : HELP_URL_DEFAULT + "/04-modality-specific-files/"
    "01-magnetic-resonance-imaging-data.html#diffusion-imaging-data",
    "fmap": HELP_URL_DEFAULT + "/04-modality-specific-files/"
    "01-magnetic-resonance-imaging-data.html#fieldmap-data",
    "func": HELP_URL_DEFAULT + "/04-modality-specific-files/"
    "01-magnetic-resonance-imaging-data.html"
    "#task-including-resting-state-imaging-data",
    "pet" : "https://docs.google.com/document/d/"
    "1mqMLnxVdLwZjDd4ZiWFqjEAmOmfcModA_R535v3eQs0/edit",
    "__unknown__" : HELP_URL_DEFAULT,
    "__ignored__" : HELP_URL_DEFAULT
}

OPTIONS_TOOLTIP_BIDSCOIN = """
bidscoin
version:    should correspond with the version in ../bidscoin/version.txt
bidsignore: Semicolon-separated list of entries that are added 
            to the .bidsignore file (for more info, see BIDS specifications),
            e.g. extra_data/;pet/;myfile.txt;yourfile.csv
            """

OPTIONS_TOOLTIP_DCM2NIIX = """
dcm2niix
path: Command to set the path to dcm2niix, e.g.:
      module add dcm2niix/1.0.20180622; (note the semi-colon at the end)
      PATH=/opt/dcm2niix/bin:$PATH; (note the semi-colon at the end)
      /opt/dcm2niix/bin/  (note the slash at the end)
      '\"C:\\Program Files\\dcm2niix\"' 
      (note the quotes to deal with the whitespace)
args: Argument string that is passed to dcm2niix. Click [Test] and see 
      the terminal output for usage
      Tip: SPM users may want to use '-z n', which produces unzipped nifti's
      """

EDITOR_EPILOG = """
examples:
    bidseditor.py /project/foo/bids
    bidseditor.py /project/foo/bids -t bidsmap_dccn.yaml
    bidseditor.py /project/foo/bids -b my/custom/bidsmap.yaml

Here are a few tips & tricks:
-----------------------------

DICOM Attributes
    An (DICOM) attribute label can also be a list, in which case 
    the BIDS labels/mapping are applies if a (DICOM) attribute value 
    is in this list. If the attribute value is empty it is not used 
    to identify the run. Wildcards can also be given, either as a single
    '*', or enclosed by '*'. Examples:
        SequenceName: '*'
        SequenceName: '*epfid*'
        SequenceName: ['epfid2d1rs', 'fm2d2r']
        SequenceName: ['*epfid*', 'fm2d2r']
    NB: Editing the DICOM attributes is normally not necessary 
    and adviced against

Dynamic BIDS labels
    The BIDS labels can be static, in which case the label is just 
    a normal string, or dynamic, when the string is enclosed with 
    pointy brackets like `<attribute name>` or `<<argument1><argument2>>`. 
    In case of single pointy brackets the label will be replaced during 
    bidsmapper, bidseditor and bidscoiner runtime by the value of the 
    (DICOM) attribute with that name. In case of double pointy brackets, 
    the label will be updated for each subject/session during bidscoiner 
    runtime. For instance, then the `run` label `<<1>>` in the bids 
    name will be replaced with `1` or increased to `2` if a file with 
    runindex `1` already exists in that directory.

Fieldmaps: suffix
    Select 'magnitude1' if you have 'magnitude1' and 'magnitude2' data 
    in one series-folder (this is what Siemens does) -- the bidscoiner 
    will automatically pick up the 'magnitude2' data during runtime. 
    The same holds for 'phase1' and 'phase2' data. See the BIDS
    specification for more details on fieldmap suffixes

Fieldmaps: IntendedFor
    You can use the `IntendedFor` field to indicate for which runs 
    (DICOM series) a fieldmap was intended. The dynamic label of 
    the `IntendedFor` field can be a list of string patterns that 
    is used to include all runs in a session that have that string 
    pattern in their BIDS file name. Example: use `<<task>>` to 
    include all functional runs or `<<Stop*Go><Reward>>` to include 
    "Stop1Go"-, "Stop2Go"- and "Reward"-runs.
    NB: The fieldmap might not be used at all if this field is left empty!

Manual editing/inspection of the bidsmap
    You can of course also directly edit or inspect the `bidsmap.yaml` 
    file yourself with any text editor. For instance to merge a set of 
    runs that by adding a wildcard to a DICOM attribute in one run item 
    and then remove the other runs in the set. See ./docs/bidsmap.md
    and ./heuristics/bidsmap_dccn.yaml for more information.
"""
