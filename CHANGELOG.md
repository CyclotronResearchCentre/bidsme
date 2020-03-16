# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

### Added
- `coinsort` now supports wildecards (\*) in recfolders, the parameter must be protected
by single quote to avoid bash expantion 
- `SubjectEndEP` and `SessionEndEP` plugins entry points for finalisation of session and subjects
- Incorporated configuration file
- logging options `level`, `quiet`, and `formatting` for log output control
- save option for saving/updating locally configuration file
- Search for map and config file in standard locations
- New command `process` that is similar to `bidsify` except do not writes on bids folder,
used for checks and processing data (via plugins)

### Fixed
- EEG naming schema discrepency with BIDS standard

### Changed
- subject and session info are managed via BidsSession class
- `participants.tsv` file now created at prepearing stage, with warning
if field values are conflicting
- Main code is `bidscoin.py` with cli command `prepare`, `bidsify` and `map`
- Plugins exit code `< 0` do not throw exception  

## [dev2.1.0] - 2020-02-19

### Fixed 
- `MRI/Nifti_SPM12`: the `JSONDecodeError` is no more cilenced in `__isValidFile` method
- bug where empty folders was created in dry mode

### Added
- plugin option to `bidsmapper`
- Support for EEG (BrainVision)

### Changed
- copy of bidsificated file(s) are performed by virtual function
`_copy_bidsified`

## [dev2.0.2] - 2020-01-27

### Added
- `time` tag for json fields that converts ms to seconds
- `getBidsPrefix` which generates `sub-..._ses-...` part of name
- Check for unchecked runs in map file
- `SetAttribute` function to manually set recording attributes
- Warning on duplicated file in `MRI/Nifti_SPM12.py:copyRawFile`

### Changed
- `Nifti_dump` becomes `Nifti_SPM12`
- Most of module functions moved to `Module/base.py` and becomes a package
- `ignoremodality` and `unknownmodality` are `Modules` global constants
- Set variable time scaling in `time` prefix for `Nifti_SPM12` 
- Moved tsv and json creation to `bidsify` function
- Simplified `tools.cleanup_value`, it removes all non ASCII alphanumeric
and add prefix, if specified
- `setSubId` and `setSesId` retrieves by default values from metadata and 
no more forom file path
- Moved Bidsmap into its own module, separated Bidsmap and Run into 2 files
- `cleanup_value` now removes etherithing not ASCII alphanumerical
and can add a prefix
- Moved `check_type` to tools
- Removed identification from folder for recordings, now `setSubId` and `setSesid`
sets to value from metadata by default
- Improved interactions with plugins
- Improved logging messages

### Removed
- subId and sesId retrieval from folder path

### Fixed
- Plugins now can import local files, their directory is added to pythonpath


## [dev2.0.1] - 2019-12-23

### Changed
- `get_dynamic_field` is rewritten to accept bids values (`<<bids:>>`), 
attributes (`<>`), values from subjects.tsv (`<<sub_tsv:>>`) and recordings.tsv 
(`<<rec_tsv:>>`)
- Moved additional json fields to yaml config file
- Updated nii template
- More explicit yaml warnings
- bidsified files are moved by copy2, the eventual post-copy actions are caried by virtual function

### Added
- json section to run, the value added to recording json file
- json section supports lists
- template section to yaml file
- `checked` field to individual run
- added placeholder field that produces warning at mapper
- special fields with a separate treatement for Nifty\_dump
- added checked field for bidsmap
- BIDSfieldLibrary can load fields from json file directly

### Fixed
- dynamic value prefix
- dynamic value ignored if it is zero or empty string
- bug in paired subject in plugin
- fixed the bool function for bidsMeta
- dynamic values conservent their type
- `get_field` values conservent their type
- in `rename_plugin.py` fixed spaces in session names
- fixed disapearance of plugin in map file
- fixet checked status reset in ignore modalities in map

## [dev2.0.0] - 2019-12-23

### Changed
- Version to 2.0.0
- Branch name to dev

### Added
- This changelog
