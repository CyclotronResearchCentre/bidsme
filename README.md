![integration test](https://github.com/CyclotronResearchCentre/bidsme/actions/workflows/integration.yml/badge.svg)
[![status](https://joss.theoj.org/papers/aeabccb41b627f6223fa2d64e17c64f8/status.svg)](https://joss.theoj.org/papers/aeabccb41b627f6223fa2d64e17c64f8)

# BIDSme

[BIDSme](https://github.com/CyclotronResearchCentre/bidsme)
is a open-source python tool that converts ("bidsifies") source-level (raw) neuroimaging 
datasets to [BIDS-conformed](https://bids-specification.readthedocs.io/en/stable).
Rather then depending on complex or ambiguous programmatic logic for the 
identification of imaging modalities, BIDSme uses a direct mapping approach to 
identify and convert the raw source data into BIDS data. The information sources 
that can be used to map the source data to BIDS are retrieved dynamically from 
source data headers (DICOM, BrainVision, nifti, etc.) and
file structure (file and/or directory names, e.g. number of files).

The retrieved information can be modified/adjusted by a set of plugins.
Plugins can also be used to complete the bidsified 
dataset, for example by parsing log files. 

> NB: BIDSme support variety of formats including nifty, dicom, BrainVision.
Additional formats can be implemented.

The mapping information is stored as key-value pairs in human-readable,
widely supported [YAML](http://yaml.org/) files, generated from a template yaml-file.


## Installation

Bidsme can be installed using pip:

```bash
python3 -m pip install git+https://github.com/CyclotronResearchCentre/bidsme.git
```

It will automatically install packages from `requirements.txt`. When treating specific data formats, additional modules may be required:

- pydicom>=1.4.2 (for DICOM images)
- nibabel>=3.1.0 (for ECAT7 images)
- mne (for various EEG/MEG recordings)

It is recommended to use virtual environment when installing bidsme (more info [here](https://github.com/CyclotronResearchCentre/bidsme_tutorial#using-virtual-environments-and-kernels) and [here](https://docs.python.org/3/library/venv.html)).

More details on how to install `bidsme` can be found in [INSTALLATION.md](INSTALLATION.md)

## How to run and examples

`bidsme` can be used with command-line interface and within Python3 shell (or script).

A extensive tutorial, aviable [there](https://github.com/CyclotronResearchCentre/bidsme_tutorial), should provide a step-by-step guidence how to bidsify a complex dataset.
The tutorial uses an example/toy dataset aviable [here](https://github.com/CyclotronResearchCentre/bidsme_examples).

Some additional documentation are aviable in `doc` directory, namely:
  - [Usage of CLI](doc/cli-interface.md)
  - [bidsification workflow](doc/workflow.md)
  - [bidsmap creation](doc/creating_map.md)
  - [plugins creation/usage](doc/plugins.md)
  - [supported data formats](doc/data_formats.md)

## How to contribute

Bugs and suggestions can be communicated by opening an [issue](https://github.com/CyclotronResearchCentre/bidsme/issues). More direct contibutions are done using [pull requests](https://github.com/CyclotronResearchCentre/bidsme/pulls).

For more informations, please refer to [contribution guide](CONTRIBUTING.md).

## Acknowledgements

`bidsme` started as a fork of [bidscoin](https://github.com/Donders-Institute/bidscoin), which can be used as an easier-to-use alternative to `bidsme`, focused on MRI datasets.

Development of `bidsme` was made possible by Fonds National de la Recherche Scientifique (F.R.S.-FNRS, Belgium) and the University of Liège.
