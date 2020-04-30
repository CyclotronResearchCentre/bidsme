# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

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
