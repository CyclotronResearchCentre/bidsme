---
title: 'Bidsme: expandable bidsifier of brain imagery datasets'
tags:
  - Python
  - BIDS
  - data management
  - standardization
authors:
  - name: Nikita Beliy
    orcid: 0009-0002-0830-3279
    equal-contrib: false
    affiliation: 1
  - name: Camille Guillemin
    orcid: 0000-0002-5377-7417
    equal-contrib: false
    affiliation: 1
  - name: Emeline Pommier
    equal-contrib: false
    affiliation: 1
  - name: Gregory Hammad
    orcid: 0000-0003-1083-3869
    equal-contrib: false
    affiliation: 1
  - name: Christophe Phillips
    orcid: 0000-0002-4990-425X
    equal-contrib: false
    affiliation: 1
affiliations:
 - name: GIGA - Cyclotron Research Centre in vivo imaging, University of Liege, Liege, Belgium
   index: 1
date: 23 November 2022
bibliography: paper.bib
---

# Summary

The purpose of Bidsme is to organize a given medical image dataset following the "Brain Image Dataset Structure" (BIDS) [@Gorgolewski2016]. Bidsme is an all-in-one organizer tool, that not only renames and re-structures the original data files, but also extracts and formats the necessary metadata. During the data organization, Bidsme provides the user with the full control over these processes, allowing the use of non-standard metadata and file names, as well as the addition of modalities not yet described by the BIDS. Instead of strictly imposing this structure, Bidsme allows the user to fully configure how the source dataset will be organized and what metadata will be included. Bidsme can be used both as Python package and command-line tool, and includes a tutorial with a test dataset.

# Statement of need

For a long time, the neuroimaging community suffered from a lack of standardized file structure, formats and metadata conventions. Different laboratories, and even different research groups within a laboratory, had their own, idiosyncratic ways to organize their data. Analyses were then performed with scripts tailored to specific data structures, which made analysis workflow and data sharing unnecessarily complicated. Consequently, it was difficult to ensure results repeatability and validation.

The Brain Image Dataset Structure (BIDS) [@Gorgolewski2016] was introduced to change this situation; it imposes a standard data structure and defines the required associated metadata. Once a dataset follows the imposed structure, any analysis tool, supporting the BIDS, should be able to automatically find the needed data to process it.

Prior to the introduction of the BIDS, the main challenge was to adapt the processing scripts to the different (typically inconsistent) dataset structures. With the advent of the BIDS, the main challenge is now to "bidsify" a given dataset, i.e. adapt a dataset to the BIDS. Not only the image files must be renamed according to the standard, but also the associated metadata must contain all expected values, using expected conventions and measurement units.

The challenge increases for datasets acquired prior to the introduction of BIDS, where often mandatory information may not even be present in the original data, or be encoded in a non-common way. This makes it difficult to use generalized tools like, e.g. [dcm2niix](https://github.com/rordenlab/dcm2niix) [@Li2016]. Any new experimental acquisition protocol may introduce new important metadata, which risks to be ignored by generalized tools. Developers will do their best to incorporate the most popular protocols, but the most exotic ones will be probably overlooked. Other tools, like, e.g. [Bidscoin](https://github.com/Donders-Institute/bidscoin) [@Zwiers2022] may rely on conventions used in the laboratory of the developers, and may be difficult to use in laboratories following different conventions.

The ideal organizer tool must be able to be flexibly adapted to any original data structure and to any reasonable laboratory practices. It must try to retrieve as much necessary metadata as possible, but also allow the user to add additional metadata. It must suggest to follow the current standard but allow deviations from it, e.g. when a given modality is not defined in BIDS.

These fundamental principles have been adopted as guidelines for the development of Bidsme. Bidsme gives full control of the data organization workflow to the user, imposing only the core of BIDS -- the directory structure, the file naming style and the global metadata. The actual names and set of entities are suggested to the user but are not imposed. Likewise, the user is free to add, remove or modify any automatically retrieved metadata.

# Bidsme overview and usage

The bidsification workflow using Bidsme is presented in \autoref{fig:workflow}. It is organized into two main steps: the "preparation" and the "bidsification".

<center>
![Workflow of a bidsification using Bidsme. Dashed arrows and boxes represent optional steps.\label{fig:workflow}](plots/bidsme_schema.png)
</center>

The preparation step organizes the dataset into BIDS-like structure, with separate directories for each subject and session. The standardized structure of the prepared dataset not only facilitates the subsequent bidsification, but also helps with visual inspection of data integrity and provides an opportunity for intervention on the dataset (e.g. with removal of corrupted or failed data samples), while keeping the original dataset untouched. Several original datasets can be prepared into the same dataset, as long as there is no overlapping data. This can be useful when bidsifying datasets with several modalities (MRI, EEG, PET).

The proper bidsification step is then performed on the prepared dataset. Bidsme scans for all data and with the help of a configuration file, i.e. `bidsmap.yaml`, it identifies each data file, generates the new bids-compliant name, and exports the desired metadata into a sidecar json file.

The aforementioned `bidsmap.yaml` configuration file is the central piece of the bidsification workflow. For each supported data format and data type (\autoref{tab:formats}), it defines a set of criteria to identify a given modality and a set of rules to bidsifiy the identified files. Identification criteria will match a given data file metadata with user-defined values, and in case of success, the bidsification rules will be applied. The file naming rules are defined as a list of entities and corresponding values, which can be either provided by the user or retrieved dynamically from the metadata. The metadata rules in the sidecar json file are defined in the same way, allowing the user to automatically export specific values from the metadata, or provide a value manually in case of missing metadata.

In addition, Bidsme implements a flexible system of plugins that can be used at any stage. A plug-in is a Python file with a set of user-implemented functions, which are executed at specific processing steps and gives access to the relevant data. Plugins allow users, for example, to rename subjects and sessions, to provide subject-related metadata, to incorporate auxiliary data (e.g. physiological) into the dataset, to add user calculated values into the metadata or to control data integrity. To help with the implementation of the plugins, Bidsme provides a template that describes the signature of the plugin functions, and a set of helper functions that implement common tasks like, for example, assembling a set 3D MRI images into one 4D MRI image, or extracting b-values from diffusion MRI image.

# Supported data types and formats

Bidsme was developed to work with multiple data types and data formats. At the time of writing, Bidsme supports MRI, PET and EEG data types and a variety of data formats, summarized in \autoref{tab:formats}.

<center>

| Modality | Data format | Module required |
| --------     | -----------        | -------------             |
| MRI        | NIfTI            | nibabel              |
|              | NIfTI+JSON  |                           |
|              | dicom          | pydicom            |
| PET        | NIfTI            | nibabel              |
|              | NIfTI+JSON  |                           |
|              | dicom          | pydicom             |
|              | ECAT            | nibabel               |
| EEG       | BrainVision   | mne                   |
|              | EDF/EDF+    | mne                   |

: List of supported data formats together with Python3 modules\label{tab:formats}
</center>

Bidsme was implemented using an object-oriented approach, where the interactions with the actual data files are implemented in base class in the Modules package. Every data type inherits from the base class and implements the BIDS requirements for that data type. Interactions with the data files are defined in a class which inherits from data type class and implements the metadata extraction, file validation, copy etc. Hence, it is relatively easy to expand Bidsme to support new data modalities and formats, simply by creating a new class and defining a handful of low-level functions. This allows users to quickly include additional data modalities, even if they are not currently supported by BIDS (for example, MEG or actigraphy data).

# Acknowledgements

This work and Nikita Beliy were supported by the Fonds National de la Recherche Scientifique (F.R.S.-FNRS, Belgium) through Grant No. EOS 30446199 and the University of Liège. Camille Guillemin was supported by University of Liege. Christophe Phillips is supported by the Fonds National de la Recherche Scientifique (F.R.S.-FNRS, Belgium).

As Bidsme was developped basing on [Bidscoin](https://github.com/Donders-Institute/bidscoin)[@Zwiers2022] package, we would like to thanks its developpers, and in particular its lead developper Marcel Zweirs.

# References
