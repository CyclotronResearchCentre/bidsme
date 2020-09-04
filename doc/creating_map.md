This is how I usually do the mapping, step-by-step. Sometimes I do some shortcuts, but I suggests to avoid them until you feel comfortable.


# Intro and definitions

There main guidelines:

  - Have a list of series per session in their expected order, useful to retrieve names and make notes
  - Prepare bidsified names beforehand, this will streamline process and avoid errors in `IntendedFor` meta-fields
  - Work on a good subject i.e. complete without deviation from protocol, without duplicated acquisition etc.
  - Work at 1 warning/error/recording at time, to remember modifications in previous step
  - Rerun map command at each occasion

Some vocabulary (just to avoid confusion):
  - recording -- an individual nii file (single volume) with its header exported as json
  - header -- a json file containing exported recording header
  - series -- a collection of recordings belonging to the same acquisition (here I use DICOM definition of term).
  - series Id -- a string identifying given series (usually the name of used protocol)
  - series no -- Acquisition number of a given series in their chronological order
  - session -- collection of series acquired in one visit
  - data type -- kind of data acquired (MRI, EEG, PET etc.)
  - data format -- format that recordings are stored (dicom, nifti, nifti+json etc.)
  - modality -- type of recording, corresponds to lowest level folder in bids structure (func, anat, dwi, beh, edf etc.)
  - suffix -- BIDS identificant differentiating different types of recording within modality, last part of bidsified name
  - entity -- a underscore-separated blocks constructing bidsified name, entity is composed of name and value, separated by dash. entity must be as uniform as possible within modality, values must be intuitive
  - map entry -- bidsmap block corresponding to one recording, starting with `provenance` field and ending with `json`

For MRI the relevant page is (there)[https://bids-specification.readthedocs.io/en/v1.2.0/04-modality-specific-files/01-magnetic-resonance-imaging-data.html]. The current proposal for MPM is (there)[https://docs.google.com/document/d/1QwfHyBzOyFWOLO4u_kkojLpUhW0-4_M7Ubafu9Gf4Gg/edit].

In following I will use `[]` to indicate context-depending variables, usually specific paths.
For example `[path-to-source-dataset]` should be replaced by by your specific path to source dataset.
Don't worry about plugins at this stage, but if in your map you find something not robust, too rigid or awkward note this in the list of your series. Do not note how, but note what. For example in MPM just note "remove reliance on series number"

If you are not sure on name to give to one entity, or suffix, just use something easy to spot, like "ToRename".

In the prepared folder data is always organized as follows:
```
sub-[subject Id]/ses-[session Id]/[data type]/[series number]-[series Id]/data
```

The bidsme log output usually cites concerning series, if not look to the line above for currently scanned series. Sometimes you need to look into the header, use the organisation to easily find correct file.


Use aliases to invoke bidsme, for ex.:
```
alias bidsme="python3 $HOME/Works/bidscoin/bidsme/bidsme.py"
alias bidsme-pdb="python3 -m pdb $HOME/Works/bidscoin/bidsme/bidsme.py"
```
so invocations becomes like:
```
bidsme map [parameters]
```

# Mapping dataset

I start with prepared dataset, stored in the `prepared` folder in my actual directory.
Bidsified dataset will be put into already existing and empty folder `bidsified`, in output directory. 

 * 0 - **Run map command**
```
bidsme map prepared bidsified
```
At first execution this will produce a map based on template.
Template is designed only to attribute correct modalities to recordings, **do not rely on pre-filled values**.

 * 1 -  **Look for errors**
  a) `Unable to identify [N] recordings`: look into `bidsified/code/bidsme/unknown.yaml`, copy one entry corresponding recording into correct modality section of `bidsified/code/bidsme/bidsmap.yaml`. Save bidsmap.yaml and go to *step 0*
  b) `ruamel error`: go to given line and fix the error in bidsmap.yaml file, usually they are unclosed quotes and spaces. Go to *step 0*
  c) `Failed: [N] examples matching several runs`. Several map entries produce same bidsified name. The names are given in the warnings preceeding error. Take one and search for it in bidsmap.yaml. You should find the entries that produced this error. If these entries are marked as checked, uncheck them (change true to false), if they are marked as template, also change true to false. Adjust suffix and bids section to produce different result, save file and go to step 0

 * 2 -  **Warnings**
If no more errors, look for warnings. Take one of the warnings, but ignore `Map contains [N] template runs`, `Map contains [N] unchecked runs`, or `Naming schema not BIDS`, they will be treated later.

  a) `[map entry]: Suffix not defined`
  Go to relevent map entry (indexes are python like starting at 0), and set correct suffix and bids entities. Remove checked and template, if present. Save and go to step 0
  b) `[series]: Placehoder found`
  Go to relevent map entry (search by protocol), and look for the string `<<placeholder>>`. Replace the string(s) by correct values for the recording. Remove template and checked, save and go to Step 0
  c) `[series]: Unable to get [field]`
  Go to relevant entry and find the faulty field, Usually it is in json section and in brackets, for ex. `<RFSpoilingPhaseIncrement>`. Replace the field by correct value (either from header, enclosed in brackets, or just by raw value). If value is unknown/not needed, replace by `~`, meaning void value. Remove template, checked, save and go to 0.

 * 3 - **Warnings `not BIDS` and `unchecked`**
Once you removed all warnings except the `not BIDS` and `unchecked`, you can treat them. If the treatment will produce warnings above, you should fix them (i.e. repeat 2.).

Open bidsmap.yaml file and find first unchecked entry (search for `checked: false`). Look if file (`provenance`) is correctly identified and has correct bidsified name (in field `example`). 

  a) Incorrect `example` value. Adjust `suffix` and `bids` values to your satisfaction. Remove `template` and go to 0.
  b1) Correct `example` value. Check `json` section, fill fields with missing values, if you know them, or how to retrieve them. If fields are unknown/unwanted, just remove them. Save and go to 0.
  b2) After b1, check remove empty fields in `json` section that do not produce `Unable to get ` warning. Fields that produce the warning must be set explicetly to `~`. Set checked to true, save and go to 3.

  
 * 4 - **Check for conflicts**
Once you don't have warnings, unchecked and hopefully templates, you can pass to next step.

**Remove all `bidsified/sub-` folders.**

Run bidsification:
```
bidsme bidsify prepared bidsified
```

You will see warnings about README and dataset\_description. Ignore it, or if you have these files, just pace them into `bidsified` folder.

Check for warnings and errors.
  a) Warning `<<placeholder>>`: redo step 2b
  b) Warning `Unable to get `: redo step 2c
  c) Error `[file] exists at destination`. You have at least 2 recordings that produced same bidsified name. Identify them. One of them can be read from log file just above errors, another can be seen in bidsmap, by searching the bidsified name (in `example` field).
    c1) If both are from same series but different recordings, you need to adjust `run` entity in `bids` section, typically you must place there `<AcquisitionNumber>`. Remove checked and go to *step 0*.
    c2) If recordings are from different series. Remove checked. Introduce into attribute new field allowing the differentiation between series and set its value. Look in the headers of both files for attributes athd differentiates. Use `SeriesNumber` only if no other options. Adjust `bids` `suffix` and `json` section to represent the first series. Copy-paste the entity just below itself, and adjust `attributes`, `bids` and `json` to match second series. Save and go to *step 0*


If you have warnings about missing `bval` and `bvec` files for diffusion, ignore them, they will be treated at plugin.

Once the `bidsify` do not produce errors, check for `bidsify` folder for possible errors, control scans.tsv file, and recordings json files. 
Pay special attention to `IntendedFor` and other cross-reference fields.
Check the names if individual recordings. They must can be easily identified. 

If any adjustement of bidsmap is performed, the procedure must be repeated from *step 0*.

