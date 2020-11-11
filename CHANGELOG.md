# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)


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
