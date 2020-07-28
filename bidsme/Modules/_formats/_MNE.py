###############################################################################
# _MNE.py contains settings and constants needed to read mne files
# It is highly inspired by mne-bids tool, all credits goes there
# https://github.com/mne-tools/mne-bids
###############################################################################
# Copyright (c) 2019-2020, University of Liège
# Author: Nikita Beliy
# Owner: Liege University https://www.uliege.be
# Credits: [Nikita Beliy]
# Maintainer: Nikita Beliy
# Email: Nikita.Beliy@uliege.be
# Status: developpement
###############################################################################
# This file is part of BIDSme
# BIDSme is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
# eegBidsCreator is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with BIDSme.  If not, see <https://www.gnu.org/licenses/>.
##############################################################################

from mne import io
from mne.io.constants import FIFF

# file-extension map to mne-python readers
reader = {'.con': io.read_raw_kit, '.sqd': io.read_raw_kit,
          '.fif': io.read_raw_fif, '.pdf': io.read_raw_bti,
          '.ds': io.read_raw_ctf, '.vhdr': io.read_raw_brainvision,
          '.edf': io.read_raw_edf, '.bdf': io.read_raw_bdf,
          '.set': io.read_raw_eeglab}

# list of coil types and associated channels types
COIL_TYPES_MNE = {
        FIFF.FIFFV_COIL_KIT_GRAD: "meggradaxial",
        FIFF.FIFFV_COIL_CTF_GRAD: "meggradaxial",
        FIFF.FIFFV_COIL_AXIAL_GRAD_5CM: "meggradaxial",
        FIFF.FIFFV_COIL_BABY_GRAD: "meggradaxial",
        FIFF.FIFFV_COIL_CTF_REF_GRAD: "megrefgradaxial",
        FIFF.FIFFV_COIL_CTF_OFFDIAG_REF_GRAD: "megrefgradaxial",
        FIFF.FIFFV_COIL_MAGNES_REF_GRAD: "megrefgradaxial",
        FIFF.FIFFV_COIL_MAGNES_OFFDIAG_REF_GRAD: "megrefgradaxial",
        FIFF.FIFFV_COIL_VV_PLANAR_T1: "meggradplanar",
        FIFF.FIFFV_COIL_VV_PLANAR_T2: "meggradplanar",
        FIFF.FIFFV_COIL_VV_PLANAR_T3: "meggradplanar",
        FIFF.FIFFV_COIL_POINT_MAGNETOMETER: "megmag",
        FIFF.FIFFV_COIL_VV_MAG_W: "megmag",
        FIFF.FIFFV_COIL_VV_MAG_T1: "megmag",
        FIFF.FIFFV_COIL_VV_MAG_T2: "megmag",
        FIFF.FIFFV_COIL_VV_MAG_T3: "megmag",
        FIFF.FIFFV_COIL_MAGNES_MAG: "megmag",
        FIFF.FIFFV_COIL_BABY_MAG: "megmag",
        FIFF.FIFFV_COIL_KIT_REF_MAG: "megrefmag",
        FIFF.FIFFV_COIL_CTF_REF_MAG: "megrefmag",
        FIFF.FIFFV_COIL_MAGNES_REF_MAG: "megrefmag",
        FIFF.FIFFV_COIL_BABY_REF_MAG: "megrefmag",
        FIFF.FIFFV_COIL_BABY_REF_MAG2: "megrefmag",
        FIFF.FIFFV_COIL_ARTEMIS123_REF_MAG: "megrefmag",
        FIFF.FIFFV_COIL_MAGNES_REF_MAG: "megrefmag",
        FIFF.FIFFV_COIL_EEG: "eeg",
        FIFF.FIFFV_COIL_NONE: "misc"
    }

meg_manufacturers = {'.sqd': 'KIT/Yokogawa', '.con': 'KIT/Yokogawa',
                     '.fif': 'Elekta', '.pdf': '4D Magnes', '.ds': 'CTF',
                     '.meg4': 'CTF'}

eeg_manufacturers = {'.vhdr': 'BrainProducts', '.eeg': 'BrainProducts',
                     '.edf': 'Unknown', '.bdf': 'Biosemi', '.set': 'Unknown',
                     '.fdt': 'Unknown'}

ieeg_manufacturers = {'.vhdr': 'BrainProducts', '.eeg': 'BrainProducts',
                      '.edf': 'Unknown', '.set': 'Unknown', '.fdt': 'Unknown',
                      '.mef': 'Unknown', '.nwb': 'Unknown'}

MANUFACTURERS = dict()
MANUFACTURERS.update(meg_manufacturers)
MANUFACTURERS.update(eeg_manufacturers)
MANUFACTURERS.update(ieeg_manufacturers)

