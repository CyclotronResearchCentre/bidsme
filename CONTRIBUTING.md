# Contributing to `bidsme`
  
### Reporting suggestions/issues
If you found a bug, an issue or have a suggestion, please feel free to communicate it through the [GutHub issues](https://github.com/CyclotronResearchCentre/bidsme/issues) or [Uliege GitLab issues](https://gitlab.uliege.be/CyclotronResearchCentre/Public/bidstools/bidsme/bidsme/-/issues).

### Sharing test data
`bidsme` has been developed in one laboratory and has been extensively tested against the data produced there. Some external data have been used for tests, but not at a large scale. Thus, some unexpected issues can arise when working with your own data. 
As it may be difficult to fix an issue without access to the data that caused it, we may request a set of your data files in order to track bugs or test suggestions. Since sharing medical data may be challenging due to the [GDPR](https://gdpr-info.eu/) restrictions and since `bidsme` does not necessarily need the actual image data to work, we suggest that you prepare synthetic data (e.g. blank image) with minimal metadata that reproduce the issue.
If creating the synthetic data is not possible, we will require your collaboration for testing and solving the issue. The speed of issue correction will depend on such collaboration (remote debugging is not fast nor fun).

### Updates related to BIDS version
The [BIDS](https://bids-specification.readthedocs.io/en/stable/) standard updates often. In the majority of cases, updates affect naming schemes and metadata definitions, and do not need an update of `bidsme`, as these changes can be incorporated into the `bidsmap.yaml` configuration file. More important changes (e.g. creation of `*_session.tsv` file) may require implementation in the plugins. 
Due to manpower shortage, we are not tracking the changes in BIDS supporting [1.2.0](https://bids-specification.readthedocs.io/en/v1.2.0/), unless requested explicitly (meaning you can request a given feature to be developed in bidsme!).

# Licence
By contributing, you agree that your contributions will be licensed under a GPL3+ License.

