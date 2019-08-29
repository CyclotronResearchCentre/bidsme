#!/usr/bin/env python

from os import path
from setuptools import setup, find_packages

# Read the version from bids.py
with open(path.join(path.dirname(__file__), 'version.txt')) as fid:
    version = fid.read().strip()

# Read the contents of the README file
with open(path.join(path.abspath(path.dirname(__file__)), 'README.md'), encoding='utf-8') as fid:
    long_description = fid.read()

# Read the contents of the requirements file
with open(path.join(path.abspath(path.dirname(__file__)), 'requirements.txt')) as fid:
    requirements = fid.read().splitlines()

setup(name                           = 'bidscoin',                          # Required
      version                        = version,                             # Required
      packages                       = find_packages(),                     # Required
      install_requires               = requirements,
      package_data                   = {'bidscoin': ['../*version.txt', 'icons/brain.ico'],
                                        '': ['*.yaml']},
      include_package_data           = True,
      scripts                        = ['bidscoin'+path.sep+'bidseditor.py',
                                        'bidscoin'+path.sep+'bidstrainer.py',
                                        'bidscoin'+path.sep+'bidsmapper.py',
                                        'bidscoin'+path.sep+'bidscoiner.py',
                                        'bidscoin'+path.sep+'rawmapper.py',
                                        'bidscoin'+path.sep+'dicomsort.py'],
      python_requires                = '>=3.6',
      setup_requires                 = ["pytest-runner"],
      tests_require                  = ["pytest", "pytest-cov", "coverage"],
      classifiers                    = ['Programming Language :: Python :: 3',
                                        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
                                        'Operating System :: OS Independent'],
      keywords                       = 'bids mri imaging neuroimaging dicom nifti pet',
      description                    = 'Converts and organises raw MRI data-sets according to the Brain Imaging Data Structure (BIDS)',
      long_description               = long_description,
      long_description_content_type  = 'text/markdown',
      author                         = 'Marcel Zwiers',
      author_email                   = 'm.zwiers@donders.ru.nl',
      url                            = 'https://github.com/Donders-Institute/bidscoin')
