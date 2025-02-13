## Supported formats

BIDSme design supports different types of data (MRI, PET, EEG...)
and various data-files formats. This is achieved using an object-oriented approach.

Each data-type is viewed as a sub-module of `Modules` and inherits from base class
`baseModule`, which defines the majority of logic needed for bidsification.

The sub-modules main classes (e.g. `Modules/MRI/MRI.py`) define the bids-related 
information for this particular data-type, like the list of needed metadata for the
JSON sidecar file or the list of modalities and entities.

Finally, for each data-type, several file-formats are treated by a separate class, 
inherited from the corresponding data-type class (e.g. `Modules/MRI/Nifti_SPM12.py`).
This class defines how to extract the needed meta-data from a particular file, how to identify
a file, and similar file-related operations.	

### <a name="mri"></a>MRI
`MRI` data-type includes all MRI images. The corresponding BIDS formatting can be
found [here](https://bids-specification.readthedocs.io/en/stable/04-modality-specific-files/01-magnetic-resonance-imaging-data.html).

It defines the following modalities:
- **anat** for [anatomical images](https://bids-specification.readthedocs.io/en/stable/04-modality-specific-files/01-magnetic-resonance-imaging-data.html#anatomy-imaging-data)
- **func** for [functional images](https://bids-specification.readthedocs.io/en/stable/04-modality-specific-files/01-magnetic-resonance-imaging-data.html#task-including-resting-state-imaging-data)
- **dwi** for [diffusion images](https://bids-specification.readthedocs.io/en/stable/04-modality-specific-files/01-magnetic-resonance-imaging-data.html#diffusion-imaging-data)
- **fmap** for [fieldmaps](https://bids-specification.readthedocs.io/en/stable/04-modality-specific-files/01-magnetic-resonance-imaging-data.html#fieldmap-data)

#### <a name="dicom"></a> DICOM
BIDSme supports the generic raw [DICOM](https://www.dicomstandard.org/) file format. 
Attributes extraction rely on [`pydicom`](https://pydicom.github.io/pydicom/stable/index.html) library.

DICOM files are identified by an extension `.dcm` or `.DCM`, and by word `DICM` placed in file at  `0x80`.

Attributes can be retrieved using both the DICOM tag or keyword (if defined).
For example `getField("(008, 0012)")` or `getField("InstanceCreationDate")` will both retrieve the same 
`Instance Creation Date`.
Tags must be **exatctly** in the form of a string formatted as follows: `"(%04d, %04d)"`, and the tag numbers
must be put in hexadecimal form without `0x` prefix -- the same way as DICOM tags are usually depicted.
Retrieved values are parsed if possible into python base values: `int`, `float`, `str`, `datetime.date`, 
`datetime.time` and `datetime.datetime`.

Nested values are retrieved using `/` separator. For example, `getField("(2005, 140f)/0/PixelPresentation")` 
will retrieve Pixel Presentation value from private tag.
The navigation follows the same structure as pydicom: `ds[0x2005, 0x140f][0]["PixelPresentation"]`.
To retrieve values with multiplicity, an index addressing each value must be used.
For example if `(0008, 0008) Image Type` is `['ORIGINAL', 'PRIMARY', 'M_FFE', 'M', 'FFE']`,
it can be accessed by `getField("ImageType/0") -> 'ORIGINAL'`. 

For convenience, during the preparation step, the full dump of DICOM header is created in the form of a JSON file
`dcm_dump_<dicom file name>.json`. 
In this dump, dataset structure is represented as dictionary, whereby multi-values and sequences are represented as lists.

#### <a name="hmriNIFTI"></a>hmriNIFTI
`hmriNIFTI` data-format denotes DICOM files converted to Nifti format by 
[hMRI toolbox](https://www.sciencedirect.com/science/article/pii/S1053811919300291) for 
[SPM12](https://www.fil.ion.ucl.ac.uk/spm/software/spm12/). 
Essentially it consists of a nifti image data and a JSON file with DICOM header dumped into it.

All recording attributes are retrieved from `acqpar[0]` dictionary within json file,
requesting directly the name of the corresponding field: `getField("SeriesNumber") -> 4`
In case of nested dictionaries, for ex. `"[CSAImageHeaderInfo"]["RealDwellTime"]`,
a field separator `/` should be used: 
```
getField("CSAImageHeaderInfo/RealDwellTime") -> 2700
```
In case of lists, individual elements are retrieved by passing the index:
```
getField("AcquisitionMatrix[3]") -> 72
```

The additional fields, that are not stored directly in JSON file, are calculated:
- **DwellTime** is retrieved from private field with tags `(0019,1018)` and converted from 
micro-seconds to seconds. 
- **NumberOfMeasurements** are retrieved from `lRepetitions` field and incremented by one.
- **PhaseEncodingDirection** are retrieved from `PhaseEncodingDirectionPositive`, and transformed 
to `1`(positive) or `-1`(negative)
- **B1mapNominalFAValues** are reconstructed from `adFree` and `alFree`. The exact reconstruction 
alghorytm is sequence dependent. 
- **B1mapMixingTime** are reconstructed from `adFree` and `alFree`. The exact reconstruction 
alghorytm is sequence dependent. 
- **RFSpoilingPhaseIncrement** are reconstructed from `adFree` and `alFree`. The exact reconstruction 
alghorytm is sequence dependent.
- **MTState** is retrieved from `[CSASeriesHeaderInfo"]["MrPhoenixProtocol"]["sPrepPulses"]` and set either 
to `On` of `Off`

> **Warning** These fields are guaranteed to be present in DICOM files generated by a Siemens scanner, in case of a different origin, their
implementation must be either patched up or performed in plugins.

> **Warning** `B1mapNominalFAValues`, `B1mapMixingTime` and `RFSpoilingPhaseIncrement` are sequence
dependent. It is unclear to me if sequences names are standard or not. If outcome of these values produces
incorrect output, the correction must be either patched or corrected in plugin.

#### <a name="bidsmeNIFTI"></a>bidsmeNIFTI
`bidsmeNIFTI` dataformat is a generic NIFTI data file with a accompaigned DICOM header created
by BIDSme from original DICOM file, as described in [MRI/DICOM](#dicom) section.
It was introduced in order to allow the user to use any DICOM converting tools without loosing any meta-data
from the initial file.

The JSON file conserves the same structure as original DICOM, with conservation of DICOM key words
if defined and tags (in form `"(%04d, %04d)"`) if not.

The expected procedure to use this format is following:

	1. DICOM dataset is prepared as described [here](#wf_prep).
	2. DICOM files are converted to NIFTI format using the tool preferred by the user; a requirement is that the tool conserves the original file
name (modulo the extention).
	3. DICOM files must be removed from prepared folder together with any JSON file created by the
converter to avoid data format mis-identifications and file double-counting.
	4 [process](#wf_process) and [bidsify](#wf_bidsify) steps will now use 
`dcm_dump_<dicom file name>.json`to identify recordings.

#### <a name=jsonNIFTI></a> jsonNIFTI
A lot of DICOM converters create a JSON file containing extracted meta-data. 
What metadata and how it is stored may vary unpredictably from one converter to another.

`jsonNIFTI` is an attempt to incorporate such converted files. 
The metadata is extracted from JSON file using the same procedure as for [hmriNIFTI](#hmriNIFTI):
```
getField("CSAImageHeaderInfo/RealDwellTime") -> 2700
```

#### <a name=NIFTI> </a> NIFTI
A generic Nifti format implements [NIfti file format](os.path.join(directory, bidsname).
It's supports `ni1` (`.hdr + .img` files), `n+1` and `n+2` (`.nii`) formats.

Nifti files are identified by extension, either `.hdr` or `.nii`, and 
the first 4 bytes of file: it must encode either `348` or `540`. 
As Nifti do not impose the endianess of file, both little and big 
endiannes are checked.

Base attributes are extracted directly from header, and conserve 
the name as defined
[here](https://brainder.org/2012/09/23/the-nifti-file-format/)
and [here](https://brainder.org/2015/04/03/the-nifti-2-file-format/),
or alternatively in `C` header file for 
[`ni1/n+1`](https://nifti.nimh.nih.gov/pub/dist/src/niftilib/nifti1.h)
and [`n+2`](https://nifti.nimh.nih.gov/pub/dist/doc/nifti2.h).
For example, the image x-dimension can be accessed by
`getAttribute("dim/1")`.

The Nifti header does not contain information used to identify given
recording, like protocol name, subject Id, Sequence etc.
To identify recordings these values must be set in plugins using
`setAttribute(name, value)` function.
If they are not set manually, a default value will be used.
If filename is formatted in bids-like way, the default subject Id 
and session Id are extracted from file name. If not, a null value `None`
will be used.

|Attribute name| Default value|
|--------------------|------------------|
|`PatientId`			| `sub-<subId>` or `None` |
|`SessionId`			| `ses-<sesId>` or `None` |
|`RecordingId`		| filename without extension |
|`RecordingNumber`	| index of current file |
|`AcquisitionTime`		| `None`|


### <a name="eeg"></a>EEG
`EEG` data-type includes all types of EEG recordings. 
The corresponding BIDS formatting can be
found [here](https://bids-specification.readthedocs.io/en/stable/04-modality-specific-files/03-electroencephalography.html).

It defines the modality **eeg**.
Outside the data files, BIDS requires also export of channels and events
(if present) data in `.tsv` files accompanied by sidecar JSON file.
