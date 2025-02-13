## Plugin configuration
Plugins in BIDSme are implemented as functions, called at 
specific times (entry point) during the execution of the main program. All of the commands `prepare`, 
`map`, `process` and `bidsify` support the plugins.

All functions must be defined in the same python file, but it is possible to include additional
files using the standard `import` instruction. The list of accepted functions is given in table below. 
Details on each of these functions can be found in [Plugins](#plugins) section

| Function | Entry point | Used for |
| ----------- | -------------- | ------------|
| `InitEP`  | At the start of program | Initialization of plugin, setting global parameters |
| `SubjectEP` | After entering subject folder | Adjustment of subject Id |
| `SessionEP` | After entering session folder | Adjustment of session Id |
| `SequenceEP` | After loading first data file in sequence | Global sequence actions |
| `RecordingEP`| After loading a new data file in sequence | Adjustment of recording parameters |
| `FileEP`| After copying a data file to its dInitEP(source: str, destination: str,estination | Any post-copy adjustment |
| `SequenceEndEP`| After processing last file in the sequence | Any post-sequence treatments |
| `SessionEndEP`| After processing all sequences in session | Any post-session treatments |
| `SubjectEndEP`| After processing last subject | Any post-subject treatments |
| `FinaliseEP`| At the end of program | Any actions needed to finalise bidsification of the dataset |

Each of the defined functions accepts only a pre-determined set of parameters, except `InitEP`, 
accepting an additional optional set of parameters, needed to setup any given plugin.

Each function is expected to return an integer return code:

- **0** -- successful execution, program continues normally
- **None** -- interpreted as **0**
- **[0-9]** -- an error in plugin occurred, program will stop execution
 and `PluginError` will be raised
- **<0** -- an error in plugin occurred, current entity will be skipped

The negative code will affect only the plugins in which skipping current entity
will have a meaning, namely `SubjectEP`, `SessionEP`, `SequenceEP` and `RecordingEP`.
For other functions, negative code is interpreted as **0**

> NB: Even if all scripts supports the same list of entry points, some of them 
are more adapted for data preparation and other for bidsification.
We recommend to perform all subject and session
identification, data retrieval and modifications of additional files during
preparation, whereby limiting bidisification  to renaming and 
copying files only. In this way, the user will be able to check, correct
and/or complete data manually. 

### <a name="plugins"></a>Plug-in functions

#### <a name="plug_init"></a> `InitEP(source: str, destination: str, dry: bool, **kwargs) -> int:`
The `InitEP` function is called immediately after the start of the main program. 
As the name indicates, it initialise the plugins, stores the global variables and the parameters.

It accepts 3 mandatory parameters:
 - **source: str**: a path to the source directory, from where the data files are processed
 - **destination: str**: a path to destination directory, where processed data will be stored
 - **dry: bool**: a switch to indicate if it is a dry-run (i.e. a test run where nothing is written to disk)

> **Warning**: `dry` parameter must be always stored as global parameter, 
and **any** file and folder modification parts in the plugins **must** be protected 
by check if `dry` is `False`:
```python
if not dry:
	do stuff
	....
```
 
 The custom additional parameters can be received via `**kwargs`. These parameters are communicated 
 to the program via `-o` option:
 ```
 -o par1=val1 -o par2=val2
 ```
 These parameters will be parsed into the dictionary and fed to `InitEP`:
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

In addition to the definition and storage of global parameters, `InitEP` can be used for loading
and parsing external files. For example, in [Example1](#ex1), the `Appariement.xlsx`
excel file, containing the list of subjects, is parced. 
The parsed excel file is used later to identify sessions and fill the `participant.tsv` file.

If `--part-template` option is not used in `coinsort`, then the template
 json file for `participants.tsv` can be done there, using 
 `BidsSession.loadSubjectFields(cls, filename: str=None)` class
 function. 
 
> In order to maintain consistency between subjects, the template json
file can be loaded only once. Subsequent loading will raise an exception.

#### <a name="plug_sub"></a> `SubjectEP(scan: BidsSession) -> int`
The `SubjectEP` function is called after entering the subject's folder. 
The main action of this function is the redefinition of subject Ids and filling of the
meta-data associated with the given subject.
The passed parameter `scan` is a `BidsSession` mutable object,
with proprieties:
- **subject**: containing current subject Id
- **session**: containing current session Id
- **in_path**: containing current path
- **sub_values**: containing a dictionary of current subject
data destined for `participants.tsv`

In order to change subject, it will suffice to change the `subject`
property of BidsSession:
```python
scan.subject = scan.subject + "patient"
```

It is not necessary to add `ses-` to the subject name, as it will be added
automatically, together with removal of all non alphanumerical characters.
In this way, subject Id is guaranteed to be bids-compatible.

`sub_values` is a dictionary with `participants.tsv` columns as keys and `None` as values.
Filling values will populate the corresponding lines in `participants.tsv`.

> The column names are normally defined by the template JSON file during the
preparation step, but they can be loaded from within the plugin
during `InitEP` execution.

#### <a name="plug_ses"></a> `SessionEP(scan: BidsSession) -> int`
`SessionEP` is executed immediately after entering the session folder, and 
is meant to modify current session Id.
It accepts the same `BidsSession` object as `SubjectId`, with not yet bidsified
names.

> Immediatly after execution of `SessionEP`, the `subject` and `session` 
properties of `scan` are bidsified and locked. No changes will be accepted, and
any attempt will raise an exception. Howether  these properties can be unlocked at the user's 
risk and peril by calling `scan.unlock_subject()` and 
`scan.unlock_session()`. Note that it can break the preparation/bidsification!

#### <a name="plug_seq"></a> `SequenceEP(recording: object) -> int`
`SequenceEP` is executed at the start of each sequence.
It can be used to perform global sequence checks and other actions checking validity.

'Passed parameter' is an actual recording containing the first loaded file (following alphabetical 
order).
The current subject and session can be accessed via `recording.subId()`
and `recording.sesId()`, but other BIDS attributes are not yet defined.

In the [Example1](#ex1), during the bidsification step, this plugin is used
to determine the destination of fieldmaps:
```python
if recid == "gre_field_mapping":
	if recording.sesId() in ("ses-HCL", "ses-LCL"):
		Intended = "HCL/LCL"
	elif recording.sesId() == "ses-STROOP":
		Intended = "STROOP"
```
The global intended variable used later in plugin to correctly fill
`IntendedFor` json file.

#### <a name="plug_rec"></a> `RecordingEP(recording: object) -> int`
`RecordingEP` is executed immediately after loading a new file in each of the
recordings. It is used for locally adapting the attributes of the recording.

For example, in [Example 1](#ex_1), the sorting plugin executes:
```python
if Intended != "":
	recording.setAttribute("SeriesDescription", Intended)
```
This replaces the `SeriesDescription` attributed with the global variable `Intended`, defined
during `SequenceEP`.

> The changed attribute can be restored to its original value by executing
`recording.unsetAttribute("SeriesDescription")`

#### <a name="plug_recEnd"></a> `FileEP(path: str, recording: object) -> int`
`FileEP` is called after the copy of the original recording file to its destination 
(prepared or bidsified folder, during preparation and bidsification, respectively).

In addition to the `recording` object, it accepts the `path` parameter containing
the path to the copied file.

The utility of this plugin is data file manipulation, for example 
the conversion into another format, or anonymisation. 
Working only on the copy of original file does not compromise the source dataset.

#### <a name="plug_seqEnd"></a> `SequenceEndEP(path: str, recording: object) -> int`
The `SequenceEndEP` is called after the treatment of all files in the sequence, 
and can be used to perform various checks and/or sequence files manipulation,
for example compressing files or packing 3D MRI images into a 4D one.

Sa in `FileEP` function, `path` parameter contains the path to the directory
where the last file of given sequence was copied. The `recording` object also
has last file in sequence loaded.

#### <a name="plug_sesEnd"></a> `SessionEndEP(scan: BidsSession) -> int`
`SessionEndEP` is executed after treating the last sequence of recording.
As there are no loaded recordings, it takes `BidsSession` as parameter. 
The mean goal of this function is checking the completedness of a given session,
and retrieving the metadata of such session, for example parcing various 
behevioral data.

#### <a name="plug_subEnd"></a> `SubjectEndEP(scan: BidsSession) -> int`
`SubjectEndEP` is executed after treating the last session of a given
subject. 
It can be used for checking if all sessions are present, and for 
retrieval of phenotype data for each given subject.

#### <a name="plug_End"></a> `FinaliseEP() -> int`
`FinaliseEP` is called in the end of programm and can be used
for consolidation and final checks on the destination dataset.
