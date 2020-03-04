# BIDScoin

[//]: # (<img name="bidscoin-logo" src="./docs/bidscoin_logo.png" alt="A BIDS converter toolkit" height="325" align="right">)

![PyPI - Python Version](https://img.shields.io/pypi/pyversions/bidscoin.svg)

- [The BIDScoin workflow](#workflow)
  * [Data preparation](#wf_prep)
  * [Data bidsification](#wf_bids)
  * [Bidsmap configuration](#wf_map)
  * [Plugin configuration](#wf_plug)
- [Examples](#examples)
  * [Dataset 1](#ex1)
- [Supported formats](#formats)
  * [MRI](#mri)
    + [Nifti\_SPM12](#Nifti_SPM12)
  * [EEG](#eeg)
    + [BrainVision](#BV)
- [Plug-in functions](#plugins)
- [Implementing additional formats](#new_formats)
- [Bidsmap file structure](#bidsmap)


BIDScoin is a user friendly [open-source](https://github.com/nbeliy/bidscoin) python toolkit that converts ("bidsifies") source-level (raw) neuroimaging data-sets to [BIDS-conformed](https://bids-specification.readthedocs.io/en/stable). 
Rather then depending on complex or ambiguous programmatic logic for the identification of imaging modalities, BIDScoin uses a direct mapping approach to identify and convert the raw source data into BIDS data. 
The information sources that can be used to map the source data to BIDS are retrieved dynamically from
source data header files (DICOM, BrainVision, nifti etc...) and file source data-set file structure 
(file- and/or directory names, e.g. number of files).

The retrieved information can be modified/adjusted by a set of plugins, described [here](#plugins).
Plugins can also be used to complete the bidsified dataset, for example by parcing log files. 

> NB: BIDScoin support variaty of formats listed in [supported formats](#formats).
Additional formats can be implemented following instructions [here](#new_formats) 

The mapping information is stored as key-value pairs in the human readable and 
widely supported [YAML](http://yaml.org/) files, generated from a template yaml-file.

## <a name="workflow"> </a>The BIDScoin workflow

The BIDScoin workfolw is composed in two steps:

  1. [Data preparation](#wf_prep), in which the source dataset is reorganazed into 
stadard bids-like structure
  2. [Data bidsification](#wf_bids), in which prepeared data is bidsified.

This organisation allow to user intervene before the bidsification in case of presence of errors,
or to complete the data manually if it could not be completed numerically.

### <a name="wf_prep"></a>Data preparation 

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
```bash
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

### <a name="wf_bids"></a>Data bidsification

Considering that the data is [prepeared](#wf_prep) together with 
[bidsmap](#wf_map) and [plugins](#wf_plug),
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


### <a name="wf_map"></a>Bidsmap configuration

Bidsmap is the central piece of BIDScoin. 
It tells how to identify any data file, and what modality and bids labels 
to attribute.

It is a configuration file written in [YAML](http://yaml.org/) format, which is a 
compromize between human readability and machine parcing.

By default this file, once created is stored within bidsified dataset in 
`code/bidscoin/bidsmap.yaml`.

The structure of a valid bidsmap is described in the section [Bidsmap file structure](#bidsmap).

The first step of creating a bidsmap is to prepare a reference dataset,
which is a subset of full dataset, containing only one or two subjects.
It is important to these subjects being complete (i.e. no missing scans)
and without errors made in protocol (no duplicated scans, scans in good order etc...).
This reference dataset will serve as a model for bidsmap.

Once the reference dataset is ready, the bidsmap is created by running the tool
`bidsmapper`:
```
usage: bidsmapper.py [-h] [-b BIDSMAP] [-t TEMPLATE] [-p PLUGIN]
                     [-o OptName=OptValue [OptName=OptValue ...]] [-v]
                     sourcefolder bidsfolder

Creates a bidsmap.yaml YAML file in the bidsfolder/code/bidscoin 
that maps the information from all raw source data to the BIDS labels.
Created map can be edited/adjusted manually

positional arguments:
  sourcefolder          The source folder containing the raw data in
                        sub-#/ses-#/run format (or specify --subprefix and
                        --sesprefix for different prefixes)
  bidsfolder            The destination folder with the (future) bids data and
                        the bidsfolder/code/bidscoin/bidsmap.yaml output file

optional arguments:
  -h, --help            show this help message and exit
  -b BIDSMAP, --bidsmap BIDSMAP
                        The bidsmap YAML-file with the study heuristics. If
                        the bidsmap filename is relative (i.e. no "/" in the
                        name) then it is assumed to be located in
                        bidsfolder/code/bidscoin. Default: bidsmap.yaml
  -t TEMPLATE, --template TEMPLATE
                        The bidsmap template with the default heuristics (this
                        could be provided by your institute). If the bidsmap
                        filename is relative (i.e. no "/" in the name) then it
                        is assumed to be located in bidscoin/heuristics/.
                        Default: bidsmap_template.yaml
  -p PLUGIN, --plugin PLUGIN
                        Path to plugin file intended to be used with
                        bidsification. This needed only for creation of new
                        file
  -o OptName=OptValue [OptName=OptValue ...]
                        Options passed to plugin in form -o OptName=OptValue,
                        several options can be passed
  -v, --version         Show the BIDS and BIDScoin version

examples:
  bidsmapper.py /project/foo/raw /project/foo/bids
  bidsmapper.py /project/foo/raw /project/foo/bids -t bidsmap_dccn
```
At first pass tool will scan reference dataset and try to guess 
correct parameters for bidsification. If he can't find correct
parameters or couldn't identify the run, a corresponding warning
or error will be shown on stdout (and reported in the log file).
These warnings and errors should be corrected before re-run of
`bidsmapper`. 
The final goal is to achieve state than `bidsmapper` will no more produce
any warnings and errors.

> NB:If bidsifigation requiers plugins, it is important to run `bidsmapper` 
with the same plugin.

Using [example 1](#ex1), the first pass of `bidsmapper` will produce around 500
warning, but they are repetetive. 

> 1WARNING MRI/001-localizer/0: No run found in bidsmap. Looking into template`

It means that give sample (first file - index `0`, of sequence `001-localizer`, 
of type `MRI`) wasn't identified in the bidsmap. `bidsmapper` will try to look 
in the template map to identify the sample. If sample is identified, then
`bidsmapper` will complete the bidsmap by information found in the template.
If sample is not identified in the template, a corresponding error will show
and samples attributes will be stored in `code/bidsmap/unknown.yaml`.
It is up to user to manually integrate this sample into bidsmap (and eventually
complete the template).

> `WARNING 002-cmrr_mbep2d_bold_mb2_invertpe/0: Placehoder found`

This warning tells that given sample is identified, but bids parameters
contains placeholder. To correct this warning it is enought to find
an corresponding entry in `bidsmap` and replaced placeholders by needed
values. 
The easiest way is to search for line `002-cmrr_mbep2d_bold_mb2_invertpe`:
```
- provenance: /home/beliy/Works/bidscoin_example/example1/renamed/sub-001/ses-HCL/MRI/002-cmrr_mbep2d_bold_mb2_invertpe/f1513-0002-00001-000001-01.nii
        example: func/sub-001_ses-HCL_task-placeholder_acq-nBack_dir-PA_run-1_echo-1_bold
        template: true
        checked: false
        suffix: bold
        attributes:
          ProtocolName: cmrr_mbep2d_bold_mb2_invertpe
          ImageType: ORIGINAL\\PRIMARY\\M\\MB\\ND\\MOSAIC
        bids: !!omap
          - dir: PA
          - task: <<placeholder>>
....
```
and replace `task: <<placeholder>>` by `task: nBack`.

> NB: If the run is edited, it is a good practice to change `template: true`
to `template: false`. It will mark that this run is no more automatically
generated from template.

> `WARNING func/0: also checks run: func/1`
This warning indicates that first run of `func` modality and second one
cheks the same scan. At first run it is normal, as samples are identified 
from template, and some overlaps are expected. If this warning remains in
subsequent passes, then the attributes of mentioned runs must be moved apart.

> `WARNING 012-t1_mpr_sag_p2_iso/0: Can't find 'ContrastBolusIngredient' attribute from '<ContrastBolusIngredient>'`
This warning means that `bidsmapper` can't extract given attribute from 
a scan. To correct the warning, cited attribute must be set manually, for ex.
in :
```
json: !!omap
          - ContrastBolusIngredient: <ContrastBolusIngredient>
```
change `<ContrastBolusIngredient>` to a used value (if contrast element is used),
or an empty string (otherwise).

> `WARNING 014-al_B1mapping/9: Naming schema not BIDS`
This warning appears when specified BIDS schema do not follows the standard. 
To correct this warning it will be enought to put bids section in bidsmap
into conform form ti the BIDS specifications. 
Alternitavly, if the deviation from the standard is intentional (e.g. 
given data type is not officialy supported by BIDS), the warning can be silenced 
by setting `checked` to `true`. 

Bidsmap contain several automatically filled fields that are to simplify the map 
adjustements:
- provenance: contains the path to the first data file matched to this run. 
This field is updated at each run of `bidsmapper`, but only if `checked` is 
false 
- example: this field shows an generated bids name for the file in `provenance`
- template: indicates if run was generated from template map. This value is 
not updated, and should be set to `false` at first manual edit
- checked: indicates if operator checked the run and is satisfied with the
results. In order to bidsify dataset, all runs must be checked.

Finally `bidscoiner` can be run of reference dataset, to assure that there 
no conflicts in definitions and the bidsified dataset is correct.



### <a name="wf_plug"></a>Plugin configuration
Plugins in BIDScoin are implemented as a functions (entry point) that are called at 
specific time during the execution of main program. All of the programs `coinsort`, 
`bidsmapping` and `bidscoiner` are support the plugin.

All functions must be defined in the same python file, but it is possible include additional
files using the usual `import` instruction. The list of accepted functions is given in table below.

| Function | Entry point | Used for |
| ----------- | -------------- | ------------|
| `InitEP`  | At the start of programm | Initialisation of plugin, setting global parameters |
| `SubjectEP` | After entering subject folder | Adjustement of subject Id |
| `SessionEP` | After entering session folder | Adjustement of session Id |
| `SequenceEP` | After loading first data file in sequence | Global sequence actions |
| `RecordingEP`| After loading a new data file in sequence | Adjustement of recording parameters |
| `FileEP`| After copiyng a data file to its dInitEP(source: str, destination: str,estination | Any post-copy adjustement |
| `SequenceEndEP`| After processing last file in the sequence | Any post-sequence treatments |
| `SessionEndEP`| After processing all sequences in session | Any post-session treatments |
| `SubjectEndEP`| After processing last subject | Any post-subject treatments |
| `FinaliseEP`| At the end of program | Any actions needed to finalise dataset |

Any of defined functions must accept a determined set of parameters, except `InitEP`, which
acept additionaly a set of optional named parameters, needed to setup any given plugin.

Each function is expected to return an ineger return code in range `[0-9]`, with `0` meaning 
succesful execution, and non-zero return code indicates an error. In the latter case, the execution of
programm will be stopped and plugin-related error will be raised.
Any exception occured within plugin function will also interupt the execution.
The returned `None` value is interpreted as succesfull execution.

#### <a name="plug_init"></a> `InitEP(source: str, destination: str, dry: bool, **kwargs) -> int:`
The `InitEP` function is called imidiatly after start of main programm. 
As name indicates, it initialise the plugin, store the global variables and parameters.

It accepts 3 mandatory parameters:
 - **source: str**: a path to the source directory, from where data files are processed.
 - **destination: str**: a path to destination directory, where processed data will be stored
 - **dry: bool**: a swithc to indicate if it is a dry-run (i.e. a test run where nothing is written to disk)

> **Warning**: `dry` parameter must be alwas stored as global parameter, 
and **any** file and folder modification parts in the plugins **must** be protected 
by check if `dry` is `False`:
```python
if not dry:
	do stuff
	....
```
 
 The custom additional parameters can be recieved via `**kwargs`. These parameters are communicated 
 to the programm via `-o` option:
 ```
 -o par1=val1 -o par2=val2
 ```
 These parameters will be parced into dictionary and feeded to `InitEP`:
 ```
 {
 	"par1": "val1",
 	"par2": "val2"
 }
 ```, 
 or from within a `bidsmap.yaml` file, in the  `Option/PlugIns/options` section, directly as a dictionary. 

The `source`, `destination` and `dry` values must be stored as global parameters, so they can
be used in other plugins:

```python
global source_path
source_path = source
```

Outside the definition and storage of global parameters, `InitEP` can be used for loading
and parcing external files. For example, in [Example1](#ex1), the `Appariement.xlsx`
exel file, containing the list of subjects is parced. 
The parced excel file is used later to identify sessions and fill the `participant.tsv` file.

#### <a name="plug_init"></a> `SubjectEP(scan: BidsSession) -> int:ool, **kwargs) -> int:`

## <a name="examples"></a>Examples

### <a name="ex1"></a>Dataset 1

## <a name="formats"></a>Supported formats

### <a name="mri"></a>MRI

#### <a name="Nifti_SPM12"></a>Nifti\_SPM12

### <a name="eeg"></a>EEG

#### <a name="BV"></a>BrainVision

## <a name="plugins"></a>Plug-in functions

## <a name="new_formats"></a>Implementing additional formats

## <a name="bidsmap"></a>Bidsmap file structure
