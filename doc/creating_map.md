# Bidsmap creation

The bidsmap creation is the most annoying and complex part of bidsification with `bidsme`.
In this instruction we tried to provide the step-by-step instructions how to create the map.


## Intro and definitions

There main guidelines:

  - Have a list of series per session in their expected order, useful to retrieve names and make notes
  - Prepare bidsified names beforehand, this will streamline process and avoid errors in `IntendedFor` meta-fields
  - Work on a good subject i.e. complete without deviation from protocol, without duplicated acquisition etc.
  - `bidme map` will stop at each error and warning, so make sure to fix errors and warnings that `bidsme` report
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
  - suffix -- BIDS identifier differentiating different types of recording within modality, last part of bidsified name
  - entity -- a underscore-separated blocks constructing bidsified name, entity is composed of name and value, separated by dash. Entity must be as uniform as possible within modality, values must be intuitive
  - map entry -- bidsmap block corresponding to one recording, starting with `provenance` field and ending with `json`

For MRI the relevant page is [there](https://bids-specification.readthedocs.io/en/v1.2.0/04-modality-specific-files/01-magnetic-resonance-imaging-data.html).

In following I will use `[]` to indicate context-depending variables, usually specific paths.
For example `[path-to-source-dataset]` should be replaced by by your specific path to source dataset.
Don't worry about plugins at this stage, but if in your map you find something not robust, too rigid or awkward note this in the list of your series. Do not note how, but note what. For example in MPM just note "remove reliance on series number"

If you are not sure on name to give to one entity, or suffix, just use something easy to spot, like "ToRename".


### Prepared data

In the prepared folder data is always organized as follows:
```
sub-[subject Id]/ses-[session Id]/[data type]/[series number]-[series Id]/data
```

### Errors/warning logs

`bidsme` will try to provide as much of information about encountered errors and warnings as possible. Read the printed log not only at error, but also before -- `bidsme` will say on which series he worked when error occurred. 

## Mapping dataset

I start with prepared dataset, stored in the `prepared` folder in my actual directory.
Bidsified dataset will be put into already existing and empty folder `bidsified`, in output directory. 

Map creation is an iterative process, `bidsme` will analyse each series in order of appearance, and will go to the next one only if previous was processed without errors.

Start with prepared dataset (in `prepared` directory) and empty bidsified dataset (in `bidsified` directory)> 

### Step 0 - New series

Execute:
```bash
bidsme map prepared bidsified
```

`bidsme` will get one series and will try to much it with the template, depending if file matches current `bidsmap`, template or no matches are found, the actions are similar:

#### Found in template

`bidsme` will put a new map entry into `bidsified/code/bidsme/bidsmap.yaml` with pre-filled bids entities and json fields from the template.
`bidsme` will complete the entities and json fields with one from BIDS that corresponds to given modality and suffix.

Depending on luck/template/data `bidsme` may show some warnings and/or errors, that must be addressed.
Independently of errors/warnings you must open the `bidsmap.yaml` file and do following actions, in order:

 - 1. Find relevant map entry (search for line `template:true` or for series name, it should appear in `provenance` field)
 - 2. Set `template` to `false`
 - 3. Check `example` field -- it will show generated bidsified name for the file in `provenance`, compare it with what you expect, then adjust `bids` section to much the expectations
 - 4. Check the json section, if you will need some custom metadata add new field.
 - 5. Go to step 0 (run map again) -- do not correct errors/warnings at this point

#### Found in bidsmap

If corresponding map entry, the field `checked` is `false`, `bidsme` will update `example`, `provenance` fields, and complete the entities and json fields.
The field `template: true` will always produce a warning that will make `bidsme` will always stop after processing this series.
You can use this for forbid `bidsme` to go further, even if series do not produce errors or warnings.

##### No Errors/Warnings
`bidsme` will consider series processed and will analyse the next one.

##### Errors/warnings
`bidsme` encountered some issues that require user input.
You must open/reload `bidsified/code/bidsme/bidsmap.yaml`:

 - 1. Find relevant map entry (search for series name, it should appear in `provenance` field)
 - 2. Identify one issue, read the error/warning message attentively (see below)
 - 3. Fix this issue
 - 4. Go to step 0 (run map again) -- it is better (at least in the beginning) to correct one issue at the time

Some classical warnings and errors:
  - `placeholder found`: The field value `<placeholder>` are the reminders that some entities/metadata are mandatory (for ex. `task` entity for `func`). This value will always produce a warning, you need to replace this value with desired one.
  - `ruamel error`: usually an extra space, this error will point to the faulty line
  - Unable to get [field]: `bidsme` can't find the requested metadata, find the mentioned field (usually in json section), and manually set the correct value, or set to `~` if this field is not needed
  - `Failed: [N] examples matching several runs`: this error indicates that there several data files in the series which will be bidsified with exactly same name. It can happen typically with multi-volumes recordings like `func` or `dwi`. You need add a new entity to `bids` section that allow to attribute different names to these files (for ex: `run: <AcquisitionNumber>` or `run: <AcquisitionNumber>`).
  - `Suffix not defined`: manually set the `suffix` field
  - `Bidsified name same as first file of recording`: This error happens when a bidsified name of current series coincide with a bidsified name of different series, both series should be mentioned in the message. You need to find both relevant map entries and modify them to ensure that bidsified names are distinct. If one of the recordings has `checked: true`, it must be changed to `checked: false` to insure that changes do not generate an error and `example` field will be updated
  - `schema not BIDS`: this warning indicates that you set up entities in the manner that are not BIDS compatible. You are invited to cross-check if the bidsified name is exactly what needed, and if so set `checked: true` to silence the warning.
  - `run [] also matches run []`: this error will raise than mentioned file will match two different map entries, referenced by their index and `provenance` field (for easier search). You need to find both map entries and ensure that `attributes` section matches only desired series.
  - ` IntendedFor value not found`: if a json section of a given map entry contain `IntendedFor` field **and** bidsified directory already contains current subject bidsified, `bidsme` will try to find if all entries from `IntendedFor` are present on in the bidsified subject and will report all missing files. You need just adapt the `IntendedFor` content to match bidsified dataset.

#### Not found in bidsmap not template (No compatible run found)
`bidsme` will create e new entry *for each file in the series* in `bidsified/code/bidsme/unknown.yaml`, with `__unknown__` modality, empty `suffix`, `bids`, `json` sections and partially filled `attributes` section.

 - 1. Identify the correct modality of the first map entry in the `unknown.yaml`
 - 2. Copy the first map entry to corresponding modality in `bidsmap.yaml`. Both `unknown.yaml` and `bidsmap.yaml` follows the same structure and copy-paste should be enough, but sometimes the spaces and tabulations becomes shifted -- you need to correct them, or you will see yaml parsing errors
 - 3. Fill the `suffix` field, leave `json` and `bids` empty -- they will be automatically filled at the next iteration
 - 4. Go to step 0 (run map again) -- it is better (at least in the beginning) to correct one issue at the time


### Step 10 - manual validation
Eventually all series in `prepared` directories will have corresponding map entry, without any errors/warnings.
`bidsme` may still show a warning `found [N] unchecked runs` and/or `found [N] template runs`.
This is reminder that not all templates map entries are removed and not all entries was manually validated.
This validation is almost final step for map creation.

You need to go trough all map entries and:

 - 1. Set `template` to `false` if it is `true`
 - 1. Check `example` field, if it is as you need
 - 2. Check `json` fields, if they contains needed information
 - 3. Remove all empty ('' and `~`) json fields
 - 3a. If both `example` and `json` are correct, set `checked` to `true`
 - 3b. If you set some modifications to map entry, rerun `map` to ensure that the modifications do not induce warnings/errors

### Step 30 -- Bidsification

Backup `bidsified/code/bidsme/bidsmap.yaml` file in safe place.

When all warnings from `bidsme map` command are fixed, it is the time to test that subject will be well bidsified by running: 
```bash
bidsme bidsify prepared bidsified
```

If there no errors, go to the next step, map is created. If there errors:

 - 1. Identify error (see below)
 - 2. Decide if error comes from data or from `bidsmap.yaml`
 - 3. Correct either data in `prepared` directory or modify `bidsmap.yaml`
 - 4. Run map on the subject where error has occurred to ensure that error was fixed `bidsme map prepared bidsified --participants sub-<XYZ>`
 - 5. Remove all `sub-*` from `bidsified` directory (be careful to not remove `code` directory it contains `bidsmap.yaml` file)
 - 6. Go to step 30 (re-run bidsification)

### Step 40 -- IntendedFor tests
In some modalities (usually `fmap`) BIDS require to define dependencies of files using `IntendedFor` metadata.
This metadata must contain the list of data paths (starting from subject root directory) that depends on current file.
`bidsme` can check if all files in `IntendedFor` are found.
To do the check, you just need to re-run `map` with already bidsified dataset:
```bash
bidsme map prepared bidsified
```

If some files are missing, you will see a warning `IntendedFor value not found` with references to faulty map entry.
You need just correct the values.


After these steps, the dataset should be bidsified. If there some new data arriving, the bidsified dataset can be completed by:
```bash
bidsme prepare source prepared --skip-in-tsv
bisdme bidsify prepared bidsified --skip-in-tsv
```

The option `--skip-in-tsv` will ensure that subjects already prepared/bidsified will not be processed again.
