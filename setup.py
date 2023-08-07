import os
import setuptools


# long description
long_description = open("README.md", "r").read()
version = open(os.path.join("bidsme", "version.txt"), "r").read().strip()

# Define classifiers
CLASSIFIERS = [
    "Development Status :: 4 - Beta",
    "Environment :: Console",
    "Intended Audience :: Science/Research",
    "License :: OSI Approved :: GNU General Public License v2 "
    "or later (GPLv2+)",
    "Natural Language :: English",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3 :: Only",
    "Programming Language :: Python :: 3.6",
    "Topic :: Scientific/Engineering :: Bio-Informatics",
    "Topic :: Scientific/Engineering :: Medical Science Apps."
    ]

# Define setup settings
setuptools.setup(
      name="bidsme",
      version=version,
      license="GPLv2+",
      description="Flexible bidsifier for multimodal datasets",
      long_description=long_description,
      author="Nikita Beliy",
      author_email="nikita.beliy@uliege.be",
      python_requires=">=3.6",
      packages=setuptools.find_packages(),
      install_requires=[
          "pandas <= 1.4.4",
          "ruamel.yaml>=0.15.35",
          "coloredlogs"
          ],
      extras_require={
          "nifti": ["nibabel"],
          "dicom": ["pydicom>=1.4.2"],
          "eeg": ["mne"],
          "all": ["nibabel", "pydicom>=1.4.2", "mne"]
          },
      entry_points={
          "console_scripts": [
              "bidsme=bidsme.main:cli_bidsme",
              "bidsme-pdb=bidsme.main:cli_bidsme_pdb"
              ]
          },
      zip_safe=False,
      classifiers=CLASSIFIERS,
      include_package_data=True
      )
