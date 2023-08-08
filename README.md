![integration test](https://github.com/github/docs/actions/workflows/integration.yml/badge.svg)

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

## Instructions and examples

`bidsme` comes with an [example/toy dataset](https://github.com/CyclotronResearchCentre/bidsme_examples), and the [tutorial](https://github.com/CyclotronResearchCentre/bidsme_tutorial).

Additianl info are aviable in `doc` folder.
