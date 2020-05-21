# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

### Changed
  - MRI: renamed MRI classes to DICOM, hmriNIFTI, bidsmeNIFTI, jsonNIFTI and 
NIFTI
  - MRI: moved json fields definitions to separate file `_<ClassName>`
  - MRI: streamlined json metafields loading

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
