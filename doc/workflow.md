## The BIDSme workflow

The BIDSme workflow is composed in two steps:

  1. [Data preparation](#wf_prep), in which the source dataset is reorganized into the standard bids-like structure
  2. [Data bidsification](#wf_bids), in which prepared data is bidsified.

This organisation allows the user to intervene before the bidsification in case of detected errors, or to complete the data manually if it could not be completed numerically.

### <a name="wf_prep"></a>Data preparation 

In order to be bidsified, dataset should be put into a form:
```
sub-<subId>/ses-<sesId>/<DataType>/<seriesNo>-<seriesId>/<datafiles>
```
where `subId` and `sesId` are the subject and session label, as defined by BIDS standard. 
`DataType` is a unique label identifying the modality of data, e.g. `EEG` or `MRI`.
`seriesNo` and `seriesId` are the unique identifiers of a given recording series,
defined as a set of recordings sharing the same recording parameters 
(e.g. a set of 2D slices from the same fMRI scan).

A generic dataset can be organized into a prepared dataset using the `prepare` command.
In addition to the parameters cited [above](#gen_cli),
some additional parameters are defined:

- `--part-template` allows to specify the path to the sidecar json file (template) used to create the future `participant.tsv` file. 
	It is expected to follow the [BIDS-defined structure](https://bids-specification.readthedocs.io/en/stable/02-common-principles.html#tabular-files). 
	It should include **all** needed column descriptions, including the mandatory `participant_id`
- `--sub-prefix` allows to specify the prefix identified the subject data in the original dataset. It can include parts of the path to the subjects folders. 
	For example, if in the original dataset the subject folders are stored in `participants` folder 
	(`participants/001`, `participants/002` etc.. ), then setting the `sub-prefix` to `participants/` 
	(note the slash) will make `prepare` search for subjects in the correct folder(s). 
	The specified path can contain a wildcard character `*`, to reach data stored in folders with different naming. For example, in case different participants 
	are stored in different folders (e.g. `patients/001` and `control/002`), both will be 
	reached by setting `--sub-prefix '*/'`. 
	If used, wildcard characters must be protected by single quote in order to avoid shell expansion. 
	Note that the non-path part of the prefix, if any, is removed from subject Id. 
	For this reason wildcard is forbidden outside the path.
- `--ses-prefix` allows to specify the session prefix in the same manner as `sub-prefix` above
- `--no-subject` and `--no-session` are mandatory to designate the case in which the original data of subjects and their respective
	sessions are not stored in dedicated folders. 
- `--recfolder folder=type` allows to specify in which folders the original data are stored, 
	and which one is the type of data.
	For example, `nii=MRI` tells that the `nii` subfolders contains MRI data. 
	The wildcard is allowed in the folder name.

`prepare` iteratively scans the original dataset and determines the subjects and sessions Ids based on the
folder names. Subject Id is derived from the name of the top-most folder, whereby session Id is derived from its sub-folder
(modulo the `prefix` parameters). 

The Ids are taken as they are, with removal of all non alphanumerical characters.
For example, if subject folder is called `s0123-control`, the subject Id will be 
`sub-s0123control`.
If the folder's name contains a prefix, that the user wants to exclude from the subject Id, this can be specified in the --sub-prefix option.
For example, with option `--sub-prefix s`, the subject folder `s0123-control` will 
result in subject Id `sub-0123control`.

If in the original dataset data is not organized in `subject/session` folders,
one should use options `--no-subject` and `--no-session`.
The session Id will be set to an empty string, and subject Id will be retrieved
from data files.

> N.B. If data are stored in subjects and sessions folders but the user prefers to set subjects and sessions Ids from data files, this can be implemented through
plugins. In the corresponding [plugin](#wf_plugin), the `session.subject` must be set 
to `None`, making it undefined. But undefined subjects and sessions make subject selection unavailable.

If the user wishes to rename subjects and/or sessions, it can be done with plug-in functions
`SubjectEP` and `SessionEP` or by renaming directly folders in the prepared dataset.

Once the data-files are identified, they are placed into prepared dataset, which follows 
loosely the basic BIDS structure:
```
sub-<subId>/ses-<sesId>/<DataType>/<Sequence>/data
```

The `sub-<subId>` and `ses-<sesId>` folders' names will be the bidsified version of subjects and sessions Ids.
Note that if the original dataset does not have sessions, the folder `sub-` will still be present, with an empty 
`<sesId>`.

The `<DataType>` folder will correspond to one of the `bidsme` defined data types, as specified in `--recfolder folder=type', and will contain 
all data files identified as being of this type.

`<Sequence>` folders will group all data files corresponding to the same recording (for example, 
different scanned volumes for the same MRI acquisition), it will be named as `<seqNo>-<secId>`
which will uniquely identify the sequence.

Note that `prepare` does not modify/convert/rename data files, only copies them.
If an actual modification of data is needed (e.g. anonymisation, or conversion),
this can be implemented either in plugin functions `FileEP`, `SequenceEndEP` or manually in the prepared
dataset. 
When manually implementing a modification in the prepared dataset, the user should ensure that the data files remain in the prepared folders and that the data format is supported 
by BIDSme. If so, [data bidsification](#wf_bids) should perform normally.

This structure has been chosen to be as rigid possible, in order to make it easier 
to treat numerically, but still human-readable.
It naturally  supports multimodal dataset.


A working example of source dataset and `prepare` configuration can be found 
[here](https://gitlab.uliege.be/CyclotronResearchCentre/Public/bidstools/bidsme/bidsme_example).

> NB: The logs for standard output and separately errors and warnings are stored
in destination folder in `code/bidsme/prepare/log` directory.

### <a name="wf_process"></a> Data processing

The processing is completely optional step between data preparation and
bidsification. It is intended to allow data modification based on data identification
of `bidsme`. For example, it can be used to check, pre-process, convert or merge data.

If plugins are not implemented, this step will only check if data are identifiable.


 

### <a name="wf_bids"></a>Data bidsification

Considering that the data are [prepared](#wf_prep) together with 
[bidsmap](#wf_map) and [plugins](#wf_plug),
the bidsification is performed by `bidsify` command:
```
bidsme.py bidsify prepared bidsified
```

It will run over data-files in prepared dataset, determine the correct modalities
and BIDS entities, extract the meta-data needed for sidecar JSON files, and 
create BIDS dataset in destination folder.

In addition to options cited [above](#gen_cli), `bidsify` accepts one additional parameter:

- `-b, --bidsmap` with path to the bidsmap file used to identify data files.
If omitted, the `bidsmap.yaml` will be used. Bidsmap will be searched first 
in local path, then in `bidsified/code/bidsme/`.

> N.B. It is advisable to first run bidsification in ["dry mode"](#gen_cli), using
switch `--dry-run`, then if no errors are detected, proceed to run bidsification in normal mode.

The subjects and session Id are by default retrieved from the folder structure, but still
can be modified in the plugins. It can be useful if the user plans to perform a random 
permutation on the subjects, to add additional layers of anonymisation. 

> NB: The log files with messages and, separately the errors are stored in
destination directory in `source/bidsme/bidsify/log` sub-directory.


### <a name="wf_map"></a>Bidsmap configuration

Bidsmap is the central piece of BIDSme. 
It allows bidsme to identify any data file, and select modalities and BIDS labels 
to attribute.

Bidsmap is a configuration file written in [YAML](http://yaml.org/) format, 
providing the optimal trade-off between human readability and machine parsing.

By default, once created, the bidsmap file is stored within the bidsified dataset in 
`code/bidsme/bidsmap.yaml`.

The structure of a valid bidsmap is described in the section [Bidsmap file structure](#bidsmap).

The first step in creating a bidsmap is to prepare a reference dataset,
which is a subset of the full dataset, containing only one or two subjects.
It is important that these subjects possess complete data (i.e. no missing scans),
organized correctly (no duplicated scans, scans in good order etc...).
This reference dataset will serve as a model for bidsmap.

Once the reference dataset is ready, the bidsmap is created by command `map`:
```
bidsme.py map prepeared/ bidsified/
```

The `map` command accepts two additional parameters:

- `-b, --bidsmap` (default: `bidsmap.yaml`), with path to the bidsmap file.
As in `bidsify` command, the given file will be searched first locally, then in 
`bidsified/code/bidsme/` directory. 
- `-t, --template` (default: `bidsmap-template.yaml`), with path to template map.
This file will be searched according to the following precedence order: local directory, default configuration directory 
(`$HOME/$XDG_CONFIG/bidsme/` on \*NIX, `\User\AppData\bidsme\` on Windows),
and `bidsme` installation directory.

At first pass, 'map' will scan the reference dataset and try to guess the
correct parameters for bidsification. If 'map' can't find the correct
parameters or could not identify the run, a corresponding warning
or error will be shown on stdout (and reported in the log file).
These warnings and errors should be corrected before re-running
`bidsmapper`. 
The final goal is to achieve a state in which the `bidsmapper` will not produce
anymore warnings and errors.

> NB:If bidsifigation requires plugins, it is important to run `bidsmapper` 
with the same plugin.

A series of notable warnings are provided below. 
These warning are generated based on the [example 1](#ex1); in this dataset, the first pass of `bidsmapper` will produce around 500
warnings.

> WARNING MRI/001-localizer/0: No run found in bidsmap. Looking into template`

This warning indicates that the given sample (first file - index `0`, of sequence `001-localizer`, 
of type `MRI`) could not be identified by 'bidsmapper'. `bidsmapper` will try to look 
in the template map to identify the sample. If sample is identified, then
`bidsmapper` will complete the bidsmap using the information found in the template.
If sample is not identified in the template, a corresponding error will show
and samples attributes will be stored in `code/bidsmap/unknown.yaml`.
It is up to the user to manually integrate this sample into bidsmap (and eventually
complete the template).

> `WARNING 002-cmrr_mbep2d_bold_mb2_invertpe/0: Placehoder found`

This warning indicates that the given sample is identified, but bids parameters
contain placeholder. To correct this warning the user should find
a corresponding entry in `bidsmap` and replace the placeholders by needed
values. 
The easiest way is to search for line `002-cmrr_mbep2d_bold_mb2_invertpe`:
```
- provenance: /home/beliy/Works/bidsme_example/example1/renamed/sub-001/ses-HCL/MRI/002-cmrr_mbep2d_bold_mb2_invertpe/f1513-0002-00001-000001-01.nii
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

> NB: If the run is edited, it is good practice to change `template: true`
to `template: false`. It will mark that this run is no more automatically
generated from template.

> `WARNING func/0: also checks run: func/1`
This warning indicates that first run of `func` modality and second one
check the same scan. This warning will normally appears during the first run, as samples are identified 
from template, and some overlaps are expected. If this warning remains in
subsequent runs, then the attributes of mentioned runs must be moved apart.

> `WARNING 012-t1_mpr_sag_p2_iso/0: Can't find 'ContrastBolusIngredient' attribute from '<ContrastBolusIngredient>'`
This warning indicates that `bidsmapper` can't extract the specified attribute from 
a certain scan. To correct the warning, the specified attribute must be set manually, for example
in :
```
json: !!omap
          - ContrastBolusIngredient: <ContrastBolusIngredient>
```
change `<ContrastBolusIngredient>` to a used value (if contrast element is used),
or an empty string (otherwise).

> `WARNING 014-al_B1mapping/9: Naming schema not BIDS`

This warning appears when specified BIDS schema do not follow the standard. 
To correct this warning, the user should modify the bids section in bidsmap
so as it conforms to the BIDS specifications. 
Alternately, if the deviation from the standard is intentional (e.g. 
given data type is not officially supported by BIDS), the warning can be silenced 
by setting `checked` to `true`. 

Bidsmap contains several automatically filled fields to simplify map 
adjustments:

  - provenience: contains the path to the first data file matched to this run. 
This field is updated at each run of `bidsmapper`, but only if `checked` is set to
'false' 
  - example: this field shows the generated bids name for the file in `provenience`
  - template: this field indicates whether run was generated from the template map or not. This value is 
not updated across runs, and should be set to `false` at first manual edit
  - checked: this field indicates whether the user checked the run and is satisfied with the
result. In order to bidsify dataset, the user should check all runs and set this field to 'true'.

Finally the `bidsify` command should be run on the reference dataset, to ensure that there are
no conflicts in definitions and the bidsified dataset is correct.
