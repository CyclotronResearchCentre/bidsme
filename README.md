# BIDSme

[BIDSme](https://gitlab.uliege.be/CyclotronResearchCentre/Public/bidstools/bidsme/bidsme)
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


## <a name="requirements"></a> Requirements

See `requirements.txt`.

### Mandatory
- python>=3.6
- pandas
- ruamel.yaml>=0.15.35
- coloredlogs

### Optional

These modules are needed for working with specific image formats:

- pydicom>=1.4.2
- nibabel>=3.1.0
- mne

## Instructions and examples

`bidsme` comes with an
[example/toy dataset](https://gitlab.uliege.be/CyclotronResearchCentre/Public/bidstools/bidsme/bidsme_example),
and the [tutorial](https://gitlab.uliege.be/CyclotronResearchCentre/Public/bidstools/bidsme/bidsme_tutorial).

Additianl info are aviable in `doc` folder.
