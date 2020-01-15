# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

### Added
- `time` tag for json fields that converts ms to seconds

### Changed
- `Nifti_dump` becomes `Nifti_SPM12`
- Most of module functions moved to `Module/base.py` and becomes a package
- `ignoremodality` and `unknownmodality` are `Modules` global constants


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
