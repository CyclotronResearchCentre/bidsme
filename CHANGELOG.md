# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

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

### Fixed
- dynamic value prefix
- dynamic value ignored if it is zero or empty string
- bug in paired subject in plugin
- fixed the bool function for bidsMeta

## [dev2.0.0] - 2019-12-23

### Changed
- Version to 2.0.0
- Branch name to dev

### Added
- This changelog
