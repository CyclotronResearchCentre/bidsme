# BIDScoin

[//]: # (<img name="bidscoin-logo" src="./docs/bidscoin_logo.png" alt="A BIDS converter toolkit" height="325" align="right">)

![PyPI - Python Version](https://img.shields.io/pypi/pyversions/bidscoin.svg)

- [The BIDScoin workflow](#the-bidscoin-workflow)
  * [Required source data structure](#required-source-data-structure)
  * [Coining your source data to BIDS](#coining-your-source-data-to-bids)
    + [Step 1a: Running the bidsmapper](#step-1a-running-the-bidsmapper)
    + [Step 1b: Running the bidseditor](#step-1b-running-the-bidseditor)
    + [Step 2: Running the bidscoiner](#step-2-running-the-bidscoiner)
  * [Finishing up](#finishing-up)
- [Plug-in functions](#options-and-plug-in-functions)
- [BIDScoin functionality / TODO](#bidscoin-functionality--todo)
- [BIDScoin tutorial](#bidscoin-tutorial)


BIDScoin is a user friendly [open-source](https://github.com/nbeliy/bidscoin) python toolkit that converts ("bidsifies") source-level (raw) neuroimaging data-sets to [BIDS-conformed](https://bids-specification.readthedocs.io/en/stable). 
Rather then depending on complex or ambiguous programmatic logic for the identification of imaging modalities, BIDScoin uses a direct mapping approach to identify and convert the raw source data into BIDS data. 
The information sources that can be used to map the source data to BIDS are retrieved dynamically from
source data header files (DICOM, BrainVision, nifti etc...) and file source data-set file structure 
(file- and/or directory names, e.g. number of files).

The retrieved information can be modified/adjusted by a set of plugins, described [here](#options-and-plug-in-functions).
Plugins can also be used to complete the bidsified dataset, for example by parcing log files. 

> NB: BIDScoin support variaty of formats listed in [supported formats](#Supported-formats).
Additional formats can be implemented following instructions [here](#Implementing-new-modalities-and-data-formats) 

The mapping information is stored as key-value pairs in the human readable and widely supported [YAML](http://yaml.org/) files,
generated from a template yaml-file.

 
## The BIDScoin workflow

The BIDScoin workfolw is composed in two steps:

  1. [Data preparation](#Data-preparation), in which the source dataset is reorganazed into stadard bids-like structure
  2. [Data bidsification](#Data-bidsification), in which prepeared data is bidsified.

This organisation allow to user intervene before the bidsification in case of presence of errors,
or to complete the data manually if it could not be completed numerically.

### Data preparation

In order to be bidsified, dataset should be put into a form:
```
sub-<subId>/ses-<sesId>/<DataType>/<seriesNo>-<seriesId>/<datafiles>
```
where `subId` and `sesId` are the subject and session label, as defined by BIDS standard. 
`DataType` is an unique label identifying the modality of data, e.g. `EEG` or `MRI`.
`seriesNo` and `seriesId` are the unique identification of given recording serie, 
which can be defined as a set of recording sharing the same recording parameters 
(e.g. set of 2D slices for same fMRI scan).

A generic data-set can be organized into prepeared datase using `coinsort` tool:
```
usage: coinsort.py [-h] [-i SUBJECTID] [-j SESSIONID] [-r RECFOLDER]
                   [-t RECTYPE] [--no-session] [--no-subject] [-p PLUGIN]
                   [-o OptName=OptValue [OptName=OptValue ...]]
                   source destination

Sorts and data files into local sub-direcories
destination/sub-xxx/ses-xxx/zzz-seriename/<data-file>

Plugins allow to modify subjects and session names
and preform various operations on data files.

positional arguments:
  source                The name of the root folder containing the recording
                        file source/[sub/][ses/]<type>
  destination           The name of the folder where sotred files will be
                        placed

optional arguments:
  -h, --help            show this help message and exit
  -i SUBJECTID, --subjectid SUBJECTID
                        The prefix string for recursive searching in
                        niisource/subject subfolders (e.g. "sub-") (default: )
  -j SESSIONID, --sessionid SESSIONID
                        The prefix string for recursive searching in
                        niisource/subject/session subfolders (e.g. "ses-")
                        (default: )
  -r RECFOLDER, --recfolder RECFOLDER
                        Comma-separated list of folders with all recording
                        files files (default: )
  -t RECTYPE, --rectype RECTYPE
                        Comma-separated list of types associated with
                        recfolder folders. Must have same dimentions.
                        (default: )
  --no-session          Dataset do not contains session folders (default:
                        False)
  --no-subject          Dataset do not contains subject folders (default:
                        False)
  -p PLUGIN, --plugin PLUGIN
                        Path to a plugin file (default: )
  -o OptName=OptValue [OptName=OptValue ...]
                        Options passed to plugin in form -o OptName=OptValue,
                        several options can be passed (default: {})

examples:
  python3 coinsort.py source renamed -r nii -t MRI
```

`coinsort` expects to have source dataset organized following
```
[<subjectId>/][<sesId>/][datafolders/]<datafiles>
```
in particular, the subject Id and session Id are extracted from the 2 top-level 
folders in source dataset. 
The Id are taking as it, with removal of all non alphanumerical characters.
For example, if subject folder is called `s0123-control`, the subject Id will be 
`sub-s0123control`.
If the folders name contain a prefix, that you don't want to be part of Id, 
you can set it with option `-i` and `-j` for subject and session.
For example with option `-i s`, the subject folder `s0123-control` will 
result in subject Id `sub-0123control`.

If in the original dataset data is not organized in `subject/session` folders,
one should use options `--no-subject` and `--no-session`.
The session Id will be set to an empty string, and subject Id will be retrieved
from data files.

If one need to rename subjects and/or sessions, it can be done with plug-in functions
`SubjectEP` and `SessionEP` or by renaming directly folders in the prepeared dataset.

`coinsort` do not modify/convert/rename data files, only copies them.
If an actual modification of data is needed (e.g. anonymisation, or convertion),
either in plugin functions `FileEP`, `SequenceEndEP` or manually in prepeared
dataset. 
As long datafiles remains in the correct folders and data format is supported 
by BIDScoin, bidsification should perform normally.

`coinsort` supports multimodal dataset.
Actually, for each data-file, `coinsort` try to determine corresponding format.
In order to help `coinsort`, and elimiate possible mis-identification, 
an option `-t RECTYPE` can be used, with provided comma-separated list of
supported data types.
The option `-r RECFOLDER` provides the list of folders where corresponding
data files are searched.
For example with option `-t MRI,EEG -r nii,eeg`, `coinsort` will look for MRI 
recordings in `<subjectId>/<sessionId>/nii` and for EEG recordings in
`<subjectId>/<sessionId>/eeg`.
If data do not have a separate folders, then an empty string `""` or 
current directory `.` can be used.

The recording directories can be nested and contain wildecards (using Unix-style 
patterns, see [glob](https://docs.python.org/3/library/glob.html) for details).
For example with `-r data/nii` data will be searched in 
`<subjectId>/<sessionId>/data/nii`.

> If wildcard characters are used, then full `RECFOLDER` must be protected
by single quote `'`, to avoid expansion by shell:
`-r '*/nii'`. In this case MRI data will be searched in all folders having
*nii* subfolder. 

A working example of source dataset and `coinsort` configuration can be found 
[there](https://github.com/nbeliy/bidscoin_example).

> NB: The logs for standard output and separetly errors and warnings are stored
in destination folder in `log` directory. 

### Data bidsification

Considering that the data is [prepeared](#Data--preparation) together with 
[bidsmap](#Creation-and-configuration-of-bidsmap-file) and [plugins](#Plugins),
the bidsification is performed by `bidscoiner` tool:
```
usage: bidscoiner.py [-h] [-p PARTICIPANT_LABEL [PARTICIPANT_LABEL ...]] [-s]
                     [-b BIDSMAP] [-d] [-v]
                     [-o OptName=OptValue [OptName=OptValue ...]]
                     sourcefolder bidsfolder

Converts ("coins") datasets in the sourcefolder to datasets
in the bidsfolder according to the BIDS standard, based on
bidsmap.yaml file created by bidsmapper. 
You can run bidscoiner.py after all data is collected, 
or run / re-run it whenever new data has been added
to the source folder (presuming the scan protocol hasn't changed).
If you delete a (subject/) session folder from the bidsfolder,
it will be re-created from the sourcefolder the next time you run
the bidscoiner.

Provenance information, warnings and error messages are stored in the
bidsfolder/code/bidscoin/bidscoiner.log file.

positional arguments:
  sourcefolder          The source folder containing the raw data in
                        sub-#/[ses-#]/run format (or specify --subprefix and
                        --sesprefix for different prefixes)
  bidsfolder            The destination / output folder with the bids data

optional arguments:
  -h, --help            show this help message and exit
  -s, --skip_participants
                        If this flag is given those subjects that are in
                        particpants.tsv will not be processed (also when the
                        --force flag is given). Otherwise the participants.tsv
                        table is ignored
  -b BIDSMAP, --bidsmap BIDSMAP
                        The bidsmap YAML-file with the study heuristics. If
                        the bidsmap filename is relative (i.e. no "/" in the
                        name) then it is assumed to be located in
                        bidsfolder/code/bidscoin. Default: bidsmap.yaml
  -d, --dry_run         Run bidscoiner without writing anything on the disk.
                        Useful to detect errors without putting dataset at
                        risk. Default: False
  -v, --version         Show the BIDS and BIDScoin version
  -o OptName=OptValue [OptName=OptValue ...]
                        Options passed to plugin in form -o OptName=OptValue,
                        several options can be passed

examples:
  bidscoiner.py /project/foo/raw /project/foo/bids
  bidscoiner.py -f /project/foo/raw /project/foo/bids -p sub-009 sub-030
```

It will run over data-files in prepeared dataset, determine the correct modalities
and BIDS entities, extract the meta-data needed for sidecar json files, and 
create BIDS dataset in destination folder.

If an option `-d` is given, `bidscoiner` will run in "dry" mode, simulating
the bidsification without actually creating and or editing any file at 
destination. 
This option is usefull to run before bidsification, in order to detect 
possible problems without compromizing dataset.

If an option `-s` is given, the participants existing in `participants.tsv`
in destination dataset are skipped.

The subjects and session Id are retrieved from folder structure, but still
can be modified in the plugins. It can be usefull if one plan perform a random 
permutation on the subjects, for additional layer of anonymisation. 

> NB: The log files with messages and, separately the errors are stored in
destination directory in `source/bidscoin/log` sub-directory.

## Options and plug-in functions
BIDScoin provides the possibility for researchers to write custom python functions that will be executed at bidsmapper.py and bidscoiner.py runtime. To use this functionality, enter the name of the module (default location is the plugins-folder; otherwise the full path must be provided) in the bidsmap dictionary file to import the plugin functions. The functions in the module should be named `bidsmapper_plugin` for bidsmapper.py and `bidscoiner_plugin` for bidscoiner.py. See [README.py](./bidscoin/plugins/README.py) for more details and placeholder code.

## BIDScoin functionality / TODO
- [x] DICOM source data
- [ ] PAR / REC source data
- [ ] P7 source data
- [ ] Nifti source data
- [x] Fieldmaps
- [x] Multi-echo data
- [x] Multi-coil data
- [x] PET data
- [ ] Stimulus / behavioural logfiles

> Are you a python programmer with an interest in BIDS who knows all about GE and / or Philips data? Are you experienced with parsing stimulus presentation log-files? Or do you have ideas to improve the this toolkit or its documentation? Have you come across bugs? Then you are highly encouraged to provide feedback or contribute to this project on [https://github.com/Donders-Institute/bidscoin](https://github.com/Donders-Institute/bidscoin).

