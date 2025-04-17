# Standing issues

Here I will puth known issues of bidsification using `bidsme` that I'm aware.


## Important
Issues that affects bidsified data/metadata

 - Extracting bval/bvec from DICOM header (also with hmriNIFTI) provide values in scanner space, not image space, as required by FSL
 

## Minor
Issues not affecting data, only bidsification process

 - [deprecation warnings with Python3.13](https://github.com/CyclotronResearchCentre/bidsme/issues/18)
 - Overflow of info/warnings messages may crash jupyther-lab
 - Outdated tutorial
 - Small discrepancies and errors in the bidsification template
