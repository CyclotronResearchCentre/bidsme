# Contributing to `bidsme`
  
### Reporting suggestions/isssues

If you found a bug, an issue or have a suggestion, please feel free to communicate it through the [GutHub issues](https://github.com/CyclotronResearchCentre/bidsme/issues) or [Uliege GitLab issues](https://gitlab.uliege.be/CyclotronResearchCentre/Public/bidstools/bidsme/bidsme/-/issues).

### Sharing test data

`bidsme` has been developped in one laboratory and has been extensively tested against the data produced there. Some exteriour data has been used for tests, but not at large scale. Thus some unexpected issues can arise when working with your data. 

We will try to fix thase issues as they arrive, but it may be difficult without access to the data that caused a given issue, so we may request a set of data files in order to track bugs or test suggestions. 

Sharing medical data may be challenging due to the [GDPR](https://gdpr-info.eu/) restrictions. Fortunally, `bidsme` does not need the image data. We woud suggest that you prepare syntetic data (for ex. blank image) with minimal metadata that reproduces an issue.

If creating the syntetic data is not possible, we will require a close collaboration in tracing the issue. The speed of issue correction will depend on this collaboration (remote debugging is not fast or fun).

### Updates related to BIDS version

The [BIDS](https://bids-specification.readthedocs.io/en/stable/) standard updates often. In majority of cases, updates consists of updates in naming schemes and metadata definitions, and do not need an update of `bidsme`, as these changes can be incorporated into `bidsmap.yaml` configuration file. More important changes (for ex. creation of `*_session.tsv` file) may require implementation in the plugins. 

Due tu manpower shortage, we are not tracking the changes in BIDS supporting [1.2.0](https://bids-specification.readthedocs.io/en/v1.2.0/), unless requested explicetly (meaning you can rewquest the support of a given feature!).