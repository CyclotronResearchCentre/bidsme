# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

### Added:
 - CITATION.cff

### Changed:
 - Python version: limited version to `<3.13`

### Fixed:
 - bidsschema: added `type`function making it compatible with bidsschematool 1.1.3
 - recId: Replacing all non word characters by `_` ([gitHub:#19](https://github.com/CyclotronResearchCentre/bidsme/issues/19))
 - Using `shutil.copyfile` instead of `shutil.copy` to avoid cros-filesystem problems
  - DICOM: parcing of `AT` type
  - Support of extension-less files (in prepare)

## [1.9.5] - 2025-08-11
### Fixed:
 - hmriNIFTI: Inverted PE direction for `j`, based on [dcm2niix](https://github.com/rordenlab/dcm2niix/blob/98ecd0bec9a1dfabd77b2be8c54c3bae97b92a55/console/nii_dicom_batch.cpp#L2426)
 - bidsmeNIFTI: Fixed custom fields overwrite when loading the file

## Added:
 - hmriNIFTI: Added more shortcuts for retrieving metadata from header, in particular DwellTime

## Changed:
 - plugins/dcm2niix: Reimplemented conversion code for dcm2niix, filenames are recovered from parcing stdout, also accepts local instalations of dcm2niix


## [1.9.4] - 2025-06-20
### Fixed:
 - `PET/bidsmeNIFTY`: Fixed extensions so compressed files should be taken into account

## [1.9.3] - 2025-06-20
### Fixed:
 - `participants_table.tsv`: Now the `N/A` are filled in case of duplicates 
 - `plugins/tools/General.py`: `SaveBval` kept `.nii` extensions if base name was a compressed image ([issue #37](https://gitlab.uliege.be/CyclotronResearchCentre/Public/bidstools/bidsme/bidsme/-/issues/37))


## [1.9.2] - 2025-05-26
 
### Fixed:
 - plugins/General: Extracted `bvec` vectors are now reoriented to the image space

## [1.9.1] - 2025-05-07

### Fixed:
 - Metadata field parcing: bug where a composite fields (like `PhaseEncodingDirection`) couldn't retrieved the raw values
 - Temporary fix for an `<<increment>>` tag resetting with every new recording
 - bidsmap: example field not filled when two different map blocks process same acquisition

### Changed:
 - plugins/tools/General/CheckPrepared: will accept also subject and session names directly to perform checks;
also will mirror the same checks configurations as CheckSeries 
 - bidsme-gui: the tkinter dependency is now optional, `bidsme` can be used without it, but attempting
to launch `bidsme-gui` will end up with `ModuleNotFoundError`
 - bidsme-gui: now launched from CLI with `bidsme-gui` command

### Added:
 - ISSUES.md: keep track of currently known issues with `bidsme`
 - plugins/nibabel: Added TR parameter in `Convert_3D_to_4D` to set the time dimention of 4D images

## [1.9.0] - 2025-02-27

### Added
 - `<<increment[1-9]:tag>>` field that will count how much this field is accessed. Useful for `run-` and `chunk-` entities. The tagless version `<<increment[1-9]>>` will count number of times the bidsified name is generated.
 - `mapper.py`: Added cals to `SessionEndEP` and `SubjectEndEP` plugin functions for consistency with `bidsify.py`
 - `GUI`: Metadata explorer

### Changed:
 - Reimplemented `getDynamicField`, now it parces tags using `regexp`, added unittest for metadata retrieval
 - `baseModule`: During preparation, bidsme will copy not only the image file, but all files sharing the same basename 
 - `tools/change_ext`: will return the basename without extention if argument `new_ext` is `None`
 - Added minimal `pyproject.toml` to silence warning

### Fixed:
 - For some file formats `dump()` was returning string instead of `dict`
 - `plugins/Nibabel/Convert3Dto4D`: Fixed bug of incrorrectly scaled concatenated image when using original scaling. This bug affects only images with slope and intersept != (1, 0)

## [1.8.2] - 2024-12-09

### Added:
 - `Module/base`: Added possibility to lock `seriesNo` and `seriesId` to avoid the retrieval of No and Id for each loaded file
 - `bidsify`, `map`: Series No and Id is retrieved from folder name and not automatically

### Changed:
 - `tools.change_ext` will return basename if `new_ext` is None
 - `Module/base`: If unable to recover series number or series id, the default values of 0 and 'unknown' will be used
 - `Module/base`: In series id, the space and tabs will be replaced by underscores
 - `Module/base`: Retriving an incorrect characteristic (`<<>>`) will pring an error to log

### Fixed:
 - `Module/jsonNIFTY`: no longer spams warnings if unable to determine series id

## [1.8.1] - 2024-09-19

### Changed:
 - `bidsmap_template`: Updated to BIDS 1.10.0 and added several new protocols
 - BIDSschema validation: BIDS-defined fields that are not defined for current data-type now raises an error
 - BIDSschema validation: Extra non BIDS fields now show a warning

### Fixed:
 - mapper: Error when testing an empty `IntendedFor` field
 - mapper: When retrieving run from template, attributes wasn't adapted to the tested file
 - MRI: `perf` data type wasn't in valid data types


## [1.8.0] - 2024-09-12

### Added
 - MRS: support for [Magnetic Resonance Spectroscopy](https://bids-specification.readthedocs.io/en/stable/modality-specific-files/magnetic-resonance-spectroscopy.html)

### Fixed
 - bidsmap: Empty modules no longer saved to bidsmap
 - bidsmap: In case of BIDS version change, warning shows incorrect version
 - hmriNIFTI: Fixed error of corrupted file on Siemens derivated MRI images lacking `CSASeriesHeaderInfo` sections

### Changed
 - bidsmap/run: If modality or suffix not defined, default model will be `__unknown__`, otherwise `<modality>:suffix`
 - bidsmap/bidsmap: For `__unknown__` and `__ignore__` modalities, the model will be fixed to `__unknown__`
 - mapper: If suffix is not defined, an error will be shown, and no further vqalidations will be performed on that file
 - BidsTable: Updated `lineterminator` parameter, making it compatible with modern (>1.4) Pandas, and Pythons up to 3.12
 - Modules: Base module class selector has been moved into tools, new modalities are no longer decalred in `selector.py`


## [1.7.1] - 2024-09-05

### Fixed
 - plugins/tools/General: in `CheckPrepared`, the check is not performed if modality folder is not present
 - jsonNIFTI: The default metadata is now correctly imported
 - setup.py: Limited numpy version to `1.26.4`, see issue [!15](https://github.com/CyclotronResearchCentre/bidsme/issues/15)

### Changed
 - `test_schema`: performing tests on `perf:asl` instead of `eeg:coordsystem`, as it was moved to json subfolder

### Removed
 - `test_schema`: Test of validity of example datasets, as examples are difficult to manage


## [1.7.0] - 2024-06-12

### Added:
 - The sidecar and entities are retrieved from official BIDS schema via `bidsschematools`
 - During mapping, the same schema is used to validate the entities and sidecars
 - unittests for schema retrieval and validation
 - plugin.tools.General: Functions for helping prepared data curation, namely LoadCurationList, CleanupPrepared and CheckPrepared
 - unittests for data curation

### Changed
 - mapping,bidsification: the list of entities and sidecar fields are extracted from current BIDS schema
(based on `bidsschematools` package)
 - Python>=3.8, Python<3.11: Restricted python to >=3.8 to satisfy dependence to `bidsschematools`
 - bidsmap: model parameter is now explicitly saved in bidsmap
 - bidsmap: model now takes form of `<data type>:<suffix>` and used to retrieve entities and sidecat fields
 - mapping: template == true will now also expand json and entities sections
 - Modules: the metadata fields in modality class definitions are now replaced by shotrcuts, which
links sidecar JSON field with corresponding dynamic field in metadata
 - bidsmap: required sidecar json fields that BIDSME can retrieve automatically (in custom variables,
via shortcuts, or directly in metadata) are now explicetly saved in bidsmap
 - unknown map is now created in same folder as bidsmap
 - DWI: warning about missing bval/vec files now triggers only for suffix dwi

## [1.6.6] - 2024-04-25

### Fixed
 - bidsify: Error when trying bidsify non-BIDS modalities ([issue #29](https://gitlab.uliege.be/CyclotronResearchCentre/Public/bidstools/bidsme/bidsme/-/issues/29))


## [1.6.5] - 2024-04-17

### Fixed
  - jsonNIFTI: fixed retrieval of ParticipantID, based on `dcm2niix` entry `PatientID`
  - BaseModule: `series_no`/`series_id` becomes prperties with type check (int/str resp.)

### Added
  - Log entry while loading tables
  - NIFTI: added support for compressed files

## [1.6.4] - 2024-04-11

### Fixed
  - logging output redirected to stdout, and forcing colors (fixing red background in jupyther-lab)
  - Import issue for MRI/DICOM when installed `pydicom` will raise error with not installed `dicom-parcer`

### Changed
  - Limited support for Python <3.11

## [1.6.3] - 2024-03-06

### Fixed
  - Plugin/Nibabel: crash in Convert3Dto4D when removing merged files

### Added
  - Plugin/Nibabel: Convert3Dto4D will also remove json files, not only nifti
  - Plugin/Nibabel: Convert3Dto4D will conserve the written data scale, if all merged files have the same slope and intercept

### Changed
  - Plugin/Nibabel: Convert3Dto4D will produce an error when trying merging of 2-file nifti (hdr/img)


## [1.6.2] - 2024-03-04

### Fixed
  - Plugins import is explicetely reset in the beginning of preparation/mapping/processing/bidsification


## [1.6.1] - 2024-02-20

### Fixed
  - Modules/MRI/bidsmeNifty: Removed error if file was created not from DICOM
  - Modules/PET/bidsmeNifty: Removed error if file was created not from DICOM

## [1.6.0] - 2024-02-19

### Added
 - Modules/base: The series Id and No can now be changed in plugins via attributes `recording.series_id` and `recording.series_no`
 - MRI/jsonNIFTY: All bids metafields are by default completed from the provided json
 - Modules/base: If BIDS metadata has the same name as a custom metadata, then the content of custom metadata is used
 - plugins/tools: A tool that uses dcm2niix to convert and merge dicoms after preparation

### Changed:
 - Modules/MRI/Nifti, Modules/PET/Nifti: the header dump is now created by default
 - MRI/DICOM: Using nibabel and mri\_parser to parse Siemens-specific headers CSAHeaderInfo and CSASeriesInfo

### Fixed
 - Modules/MRI/Nifti, Modules/PET/Nifti: diminfo from header are now retrieved as integer instead of bytes
 - Modules/MRI/Nifti, Modules/PET/Nifti: header dump exported as dict, instead of string


## [1.5.1] - 2023-12-19

### Fixed
 - Module/MRI/hmriNIFTY: Extra error log, if encountered standard json instead of hmriNIFTY json

## [1.5.0] - 2023-11-22

Release for the publication in JOSS

### Fixed
 - Module/base: Bug when  `recIdentity()` wasn't called as function

### Changed
 - Several improvements in documentation and README
 - Updated links to the examples and tutorial to point to GitHub

## [1.4.3] - 2023-08-17
### Fixed:
 - Bug in bidsification when working with bare nifty file

## [1.4.2] - 2023-08-08
### Added:
 - Integrartion test for GitHub
### Changed:
  - Table sidecars (including participants.json) now supports extra phields, not related to columns names

## [1.4.1] - 2023-07-12

### Fixed:
  - PET: Updated entities list, remobved some nore more required json metadata
  - PET/ECAT: Degraded warning of non-decodable bytes string to debug
  - plugins/template: Fixed (finally) the import of classes in template

### Changed:
  - bidsmap: Accepting non-bids modality with a warning
  - bidsmap: Runs loaded from template are now unchecked
  - README.md: liknks points to GitHub repo

## [1.4.0.post4] - 2022-10-17

### Fixed:
  - MRI/jsonNIFTY, PET/jsonNIFTY: fixed crash when trying to load generic json NIFTY file
 
## [1.4.0.post3] - 2022-06-15

### Fixed:
 - MRI/hmriNIFTY: removed requirement of presence of `MrPhoenixProtocol`  

### Changed:
 - Splitted bloated README

## [1.4.0.post2] - 2022-05-06

### Changed
 - Version naming schema for post-release fixes

### Fixed
 - `plugins`: added `__init__.py` to tools so plugin tools will be properly installed

## [1.4.0r1] - 2022-05-05

### Removed
 - `baseModule`: removed spanning messages about testing files in scan folders

### Fixed
 - `bidsMeta`: Fixed not reseted bidsSession list of `subjects.tsv` columns
 - `plugins.tools`: Fixed faulty import of `baseModule`

## [1.4.0] - 2022-05-02

### Changed
 - Rearranged imports to be importable as module
 - Moved `version.txt` and `bidsversion.txt` to bidsme sub-folder
 - Moved heuristics folder to bidsme directory

### Added
 - `bidsme` now is installable with pip, and importable as module
 - `setup.py` scripts for setuptools
 - `tools.info.reseterrors()` function to reset error counters

### Removed
 - `tests` directory, to be reintegrated later
 - reload participants definition warning


## [1.3.6] - 2022-04-26

### Changed
  - map: by default `bidsme map` will stop after first recording producing
error/warnings. Added a CLI parameter `--process-all` to process all recordings
in one go.
  - BaseModule: more explicit messages for testing validity of files at 
DEBUG level

### Added
  - map: check for several files ending up with same bidsified name
  - Support for CT in PET data type

### Fixed:
  - Small misprint that forbids the dump of DICOM header in PET
  - few adjustements in parcing DICOM header
  - map: checks for `IntendedFor` field wasn't running in multisession datasets
  - BidsSession: bug when `sub_values` not intended for `participants.tsv` are
  - EEG, \*NIFTI: Fixed returnvalue for copyRawFile
  - PET: Updated recommended and required sidecar metadata
checked for changes

## [1.3.5r9] - 2022-03-04

### Fixed
  - hmriNIFTI: fixed incorrect PhaseEncodingDirectionSign default value

## [1.3.5r8] - 2021-11-22

### Fixed
  - bug with option `--skip-existin-session` not working in preparation

## [1.3.5r7] - 2021-10-27

### Fixed
  - duplicated entries in `participant.tsv` wasn't saved in `__duplicates.tsv`

## [1.3.5r6] - 2021-10-08

### Fixed
  - NRI/hmriNIFTI: fixed error while retrieving `afFree` and `adFree`
firlds when they are not defined in json file

## [1.3.5r5] - 2021-08-18

### Fixed
  - DICOM: fixed crash if patient age is not defined 
  - DICOM: persons name is decoded correctly
  - DICOM: if DS or IS not defined, returned value is None

### Added
  - MRI/DICOM and PET/DICOM: support for extentions `.ima` and `.IMA`
  - MRI/DICOM: `MRAcquisitionType` metafield
  - MRI: set of recommended fields for qMRI
  - DICOM: added exception if decoding a particular value from header
produces an error

## [1.3.5r4] - 2021-07-20

### Fixed
  - MRI: misspell in the name of `RepetitionTimeExcitation`

## [1.3.5r3] - 2021-06-16

### Changed
  - participants.tsv table is managed using bidsMeta.BidsTable class

### Fixed
  - MRI/NIFTI and PET/NIFTI: incorrect parameter for `retrieveFormDict`

## [1.3.5r2] - 2021-03-10

### Fixed
  - jsonNIFTI, hmriNIFTI: file parts parcing for compressed files


## [1.3.5r1] - 2021-03-01

### Changed
  - bidsify: Allow conflicting values for `participants.tsv`. These values will be reported in `__duplicated.tsv` and 
must be merged manually with `participants.tsv`
  - baseModule: Set index before loading file. If loading crashes, now it should report correct file

### Added
  - hMRI: test for `CSASeriesHeaderInfo`, `CSAImageHeaderInfo` and `MrPhoenixProtocol` in Siemens files. Should detect corrupted files before processing them

## [1.3.5] - 2021-02-11

### Added
  - Extra try/catch to protect running main loop, should stop crashes in case of corrupt data

### Fixed
  - baseModule: Bidsified file is compressed only if he wasn't compressed before, the correct extention `.gz` is added to scans.tsv content
  - mapper: IntendedFor fields are checked from subject folder, the widecar characters are disallowed

### Changed
  - MPM parameters updated


## [1.3.4] - 2020-12-29

### Added
  - MRI: `RepititionTimeExitation` json field for all modalities
  - hmriNIFTI: Support of zipped (`.nii.gz`) data files
  - baseModule:isValidFile incorporates the file extention check before calling
`_isValidFile`. The list of valid extentions must be given in `_file_extentions`
static variable in subclass
  - bidsmap: Introduced models, that allows to choose different set of entities and
json fields for given modality

### Changed
  - baseModule: moved `zip` field to `switches` dictionary
  - baseModule: renamed and inverted `isBidsValid` to `exportHeader` and moved it to `switches`
  - Moved `BidsSession` and `bidsMeta` to `bidsMeta` folder, should remove conflict with `bids` package

## [1.3.3] - 2020-11-19

### Changed
  - baseModule: testAuxiliary no longer prodices warning if unable to retrieve asked field
  - Improved bidsmap template

## [1.3.2] - 2020-11-15
### Added
  - base:getField: can have multiple prefixes, that are executed from right to left
  - mapper.py:implemented check for `IntendedFor` JSON fields. If during `map` bidsified
file exists, mapper checks if all files in IntendedFor also exist

### Changed
  - MRI:hmriNIFTI: B1FAValues vector is no longer sorted

## [1.3.1r3] - 2020-11-11

### Fixed
  - mapper.py: subject demographics are now copied into `sub_values` dictionary
  - hmriNIFTI: field `B1mapNominalFAValues` are now calculated correctly

## [1.3.1r2] - 2020-11-02

### Fixed
  - Bug when SequenceEndEP called without outfolder parameter in bidsification step
  - Several flake8 issues

## [1.3.1r1] - 2020-10-22

### Fixed
  - Fixed mandatory requirement for mne module

## [1.3.1] - 2020-10-08

### Added
  - plugins/tools/General: ExtractBval function to extract bval/vec from DWI recording
  - plugin/tools/General: storeSource function that allows store prepared data into bidsified folder
  - plugins/tools/Nibabel: Convert3Dto4D function to merge 3D nii files into 4D


## [1.3.0] - 2020-09-28

### Fixed
  - Removed miliseconds in acqTime output, as BIDS requires

### Added
  - EEG/EDF implementation using mne interface. Channels and events incorporated
  - EEG/BV implementation using mne interface.
  - map: map sanity checking, detecting duplicated provenance an examples
  - bidsmap: warning if bids value is not string, and forcefull convertion into string
  - baseModule: New public boolean switch `zip`, which is set to `False` by default.
If in plugin (in `RecordingEP` or in `SequenceEP`) is set to `True`,
then data file will be zipped during bidsification
(provided is zipping is implemented for given type)
  - plugins: tools to use in pligins. To import use `import plugins.tools.General.<toolname>`

## [1.2.1] - 2020-08-18

### Changed
  - Reloading participant template now produce warning instead of raising exception,
this should allow multiple execution in same session

### Fixed
  - \_formats:dummy Fixed conditional imports 

## [1.2.0] - 2020-08-07

### Added
  - baseModule: added a dummy class that's loads instead of format subclass if
dependancy module is not loaded
  - PET: new module for PET images
  - PET: DICOM file format
  - PET: ECAT file format
  - BaseModule: custom attributes, that can be set by `recording.custom[<name>]`,
and accessed from bidsmap using `<<custom:name>>`

### Changed
  - baseModule: moved pure virtual methodes to `Module/abstract.py`,
abstractmethode are now declared using ABC module 
  - baseModule: acquisition time is now stored in `_acqTime` attribute,
so it can be directly set by `setAcqTime(datetime)` function. The value
from header is retrieved via `_getAcqTime` virtual function
  - DICOM: when exporting header, if `AcquisitionDateTime` field is not defined
it is exported using the current recording acquisition time
  - DICOM: common dicom operations (DataElement transformation, tag search etc.)
are moved to `_dicom_common.py`
  - selector: dictionary of aviable classes is now ordered
  - bidsmeNIFTI: changed the way the header is written
  - header is automatically created if `isBidsValid` is set to false
  - pyDicom is an optional dependency

### Fixed
  - PET:ECAT Magic string test now "MATRIX" instead of "MATRIX72"
  - PET:ECAT frames headers are now exported into json
  - PET:ECAT FramesStart and Duration are now in s instead of ms
  - baseModule: fixed `copyRawFile` function to return correct path to copied file
  - baseModule: fixed access values from participants and scans tables
  - prepare: session.getPath returns correct session path is run with no-session option

## [1.1.2] - 2020-05-22

### Added
  - DICOM: unittests 

### Changed
  - MRI: renamed MRI classes to DICOM, hmriNIFTI, bidsmeNIFTI, jsonNIFTI and 
NIFTI
  - MRI: moved json fields definitions to separate file `_<ClassName>`
  - MRI: streamlined json metafields loading
  - folder recording will no longer automatically fail `isValidFile`
  - scans.tsv show acqTime with microseconds

### Fixed
  - DICOM: empty value for Time and DateTime fields
  - baseModule: virtual dump function returned exception instead of raising it
  - prepare: fixed manual setting for path in series

## [1.1.1] - 2020-05-15

### Fixed
  - prepare: now directories in folder with data files will no longer crash,
but still produce warning
  - map: in case of multiple checked runs, now the first one is used to set up
modality and labels
  - map: bug where 0 or '' values to check are not retained for bidsmap file
  - bug during attribute checking where retrieved attribute was cleaned

### Added
  - Modules: `common.py` file with often used functions for modules implementations
  - `common.py`: `action_value` function that apply a given action to value,
used for transformation of metadata from headers
  - `common.py`: `retrieveFormDict` function that implements search of value
from path in standard dictionary
  - unittests for `common.py`

### Changed
  - meta-fileds are not longer checked for pre-defined value if present in bidsmap

## [1.1.0] - 2020-05-10

### Fixed
  - MRI: fixed misspell in `FlipAngle` metafield
  - Hidden files wasn't skipped prpoerly
  - MRI: fixed order of entities for `anat` modality
  - map: crash if `<<bids:xxx>>` used if corresponding entity not set

### Added
  - MRI: headNIFTI -- NIFTI file format with bidsme-extracted DICOM-header

### Changed
  - map: `unknown.yaml` file now replicates standard `bidsmap.yaml` structure with
the only modality `__unknown__`. Copiyng directly from `unknown.yaml`, and filling
attributes, bids and suffix should now suffice for bidsmap
  - map: If bids section is empty for matched run, it will be filled by predefined
entities, provide the modality is defined in Bids standard


## [1.0.3] - 2020-05-05

### Fixed
  - `participants.tsv` wasn't filled in preparation step

### Changed
  - `map`, `process` and `bidsify` looks for given bidsmap file first in order: 
in destination code folder, local folder, and user configuration folder
  - in bidsmap `Options` dictionary is removed, and `version` entry is replaced
by `__bids__`, that refers to version of BIDS and no more to version of software,
the `bidsignore` is dropped

## [1.0.2] - 2020-04-30

### Added
  - Map attributes now accepts dynamic fields, if corresponding attribute is
included in brackets

### Changed
  - EEG:BrainVision: removed `PatientId`, `SessionId` and `RecordingNumber`
from attributes
  - EEG:BrainVision: functions `getSubId` and `getSesId` returns `None`
  - If subject Id and session Id is set to None, the corresponding values
are extracted from file name, assumming it is formatted following BIDS 
(fields `sub` and `ses` respectively)
  - If map attributes dictionary is empty, it will match all recordings
  - If map attribute is not found in recording, it will fail match
  - If map attribute is `None` then it will match all values
  - BidsSession: BidsSession class can be initialized with subject and 
session values. If these values are set, corresponding attributes will 
be locked
  - Preparation: if subject or session values are `None`, they are calculated
for each recording in serie

### Fixed
  - EEG:BrainVision: fixed `_loadFile` function name
  - EEG:BrainVision: added `acq` to template map
  - EEG:BrainVision: Fixed TaskName and SamplingFrequency json fields


## [1.0.1] - 2020-04-20

### Changed
  - Reimplementation of required, recommended and optional metadata JSON fields
  - added `acq` to `eeg` modality (present in BIDS 1.2.0)

### Added
  - `ieeg` and `meg` modalities to `EEG` module

## [1.0.0] - 2020-04-08

### Added
  - Gitlab CI
