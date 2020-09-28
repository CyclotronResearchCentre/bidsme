###############################################################################
# _MNE.py provides additional parameters for EEG classes that uses mne library
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

metafields = {
        "Unknown": {
            "PowerLineFrequency": ("<line_freq>", None),
            "SamplingFrequency": ("<sfreq>", None),
            "RecordingDuration": ("<RecordingDuration>", None),
            "RecordingType": ("<RecordingType>", None),
            "MEGChannelCount": ("<MEGChannelCount>", None),
            "MEGREFChannelCount": ("<MEGREFChannelCount>", None),
            "ECOGChannelCount": ("<ECOGChannelCount>", None),
            "SEEGChannelCount": ("<SEEGChannelCount>", None),
            "EEGChannelCount": ("<EEGChannelCount>", None),
            "EOGChannelCount": ("<EOGChannelCount>", None),
            "ECGChannelCount": ("<ECGChannelCount>", None),
            "EMGChannelCount": ("<EMGChannelCount>", None),
            "MiscChannelCount": ("<MiscChannelCount>", None),
            "TriggerChannelCount": ("<TriggerChannelCount>", None)
        }
}

# Following definitions are copied directly from mne-bids module
# All credits goes there

# Orientation of the coordinate system dependent on manufacturer
ORIENTATION = {'.sqd': 'ALS', '.con': 'ALS', '.fif': 'RAS', '.pdf': 'ALS',
               '.ds': 'ALS'}

UNITS = {'.sqd': 'm', '.con': 'm', '.fif': 'm', '.pdf': 'm', '.ds': 'cm'}

meg_manufacturers = {'.sqd': 'KIT/Yokogawa', '.con': 'KIT/Yokogawa',
                     '.fif': 'Elekta', '.pdf': '4D Magnes', '.ds': 'CTF',
                     '.meg4': 'CTF'}

eeg_manufacturers = {'.vhdr': 'BrainProducts', '.eeg': 'BrainProducts',
                     '.edf': 'Unknown', '.bdf': 'Biosemi', '.set': 'Unknown',
                     '.fdt': 'Unknown'}

ieeg_manufacturers = {'.vhdr': 'BrainProducts', '.eeg': 'BrainProducts',
                      '.edf': 'Unknown', '.set': 'Unknown', '.fdt': 'Unknown',
                      '.mef': 'Unknown', '.nwb': 'Unknown'}

# file-extension map to mne-python readers
reader = {'.con': io.read_raw_kit, '.sqd': io.read_raw_kit,
          '.fif': io.read_raw_fif, '.pdf': io.read_raw_bti,
          '.ds': io.read_raw_ctf, '.vhdr': io.read_raw_brainvision,
          '.edf': io.read_raw_edf, '.bdf': io.read_raw_bdf,
          '.set': io.read_raw_eeglab}

# Merge the manufacturer dictionaries in a python2 / python3 compatible way
MANUFACTURERS = dict()
MANUFACTURERS.update(meg_manufacturers)
MANUFACTURERS.update(eeg_manufacturers)
MANUFACTURERS.update(ieeg_manufacturers)

# List of synthetic channels by manufacturer that are to be excluded from the
# channel list. Currently this is only for stimulus channels.
IGNORED_CHANNELS = {'KIT/Yokogawa': ['STI 014'],
                    'BrainProducts': ['STI 014'],
                    'n/a': ['STI 014'],  # for unknown manufacturers, ignore it
                    'Biosemi': ['STI 014']}

allowed_extensions_meg = ['.con', '.sqd', '.fif', '.pdf', '.ds']
allowed_extensions_eeg = ['.vhdr',  # BrainVision, accompanied by .vmrk, .eeg
                          '.edf',  # European Data Format
                          '.bdf',  # Biosemi
                          '.set',  # EEGLAB, potentially accompanied by .fdt
                          ]

allowed_extensions_ieeg = ['.vhdr',  # BrainVision, accompanied by .vmrk, .eeg
                           '.edf',  # European Data Format
                           '.set',  # EEGLAB, potentially accompanied by .fdt
                           '.mef',  # MEF: Multiscale Electrophysiology File
                           '.nwb',  # Neurodata without borders
                           ]

ALLOWED_EXTENSIONS = {'meg': allowed_extensions_meg,
                      'eeg': allowed_extensions_eeg,
                      'ieeg': allowed_extensions_ieeg}

# allowed BIDS entities
BIDS_PATH_ENTITIES = ('subject', 'session', 'task', 'acquisition',
                      'processing', 'run', 'recording',
                      'space', 'suffix', 'prefix')

# accepted BIDS formats, which may be subject to change
# depending on the specification
BIDS_IEEG_COORDINATE_FRAMES = ['acpc', 'pixels', 'other']
BIDS_MEG_COORDINATE_FRAMES = ['ctf', 'elektaneuromag',
                              '4dbti', 'kityokogawa',
                              'chietiitab', 'other']
BIDS_EEG_COORDINATE_FRAMES = ['captrak']

# accepted coordinate SI units
BIDS_COORDINATE_UNITS = ['m', 'cm', 'mm']

# mapping from BIDs coordinate frames -> MNE
BIDS_TO_MNE_FRAMES = {
    'ctf': 'ctf_head',
    '4dbti': 'ctf_head',
    'kityokogawa': 'ctf_head',
    'elektaneuromag': 'head',
    'chietiitab': 'head',
    'captrak': 'head',
    'acpc': 'ras',
    'mni': 'mni_tal',
    'fs': 'fs_tal',
    'ras': 'ras',
    'voxel': 'mri_voxels',
    'mri': 'mri',
    'unknown': 'unknown'
}
MNE_TO_BIDS_FRAMES = {val: key for key, val in BIDS_TO_MNE_FRAMES.items()}

# these coordinate frames in mne-python are related to scalp/meg
# 'meg', 'ctf_head', 'ctf_meg', 'head', 'unknown'
# copied from "mne.transforms.MNE_STR_TO_FRAME"
MNE_STR_TO_FRAME = dict(
    meg=FIFF.FIFFV_COORD_DEVICE,
    mri=FIFF.FIFFV_COORD_MRI,
    mri_voxel=FIFF.FIFFV_MNE_COORD_MRI_VOXEL,
    head=FIFF.FIFFV_COORD_HEAD,
    mni_tal=FIFF.FIFFV_MNE_COORD_MNI_TAL,
    ras=FIFF.FIFFV_MNE_COORD_RAS,
    fs_tal=FIFF.FIFFV_MNE_COORD_FS_TAL,
    ctf_head=FIFF.FIFFV_MNE_COORD_CTF_HEAD,
    ctf_meg=FIFF.FIFFV_MNE_COORD_CTF_DEVICE,
    unknown=FIFF.FIFFV_COORD_UNKNOWN
)
MNE_FRAME_TO_STR = {val: key for key, val in MNE_STR_TO_FRAME.items()}

# see BIDS specification for description we copied over from each
COORD_FRAME_DESCRIPTIONS = {
    'ctf': 'ALS orientation and the origin between the ears',
    'elektaneuromag': 'RAS orientation and the origin between the ears',
    '4dbti': 'ALS orientation and the origin between the ears',
    'kityokogawa': 'ALS orientation and the origin between the ears',
    'chietiitab': 'RAS orientation and the origin between the ears',
    'captrak': 'RAS orientation and the origin between the ears',
    'mri': 'Defined by Freesurfer, the MRI (surface RAS) origin is at the '
           'center of a 256×256×256 1mm anisotropic volume '
           '(may not be in the center of the head).',
    'mri_voxel': 'Defined by Freesurfer, the MRI (surface RAS) origin '
                 'is at the center of a 256×256×256 voxel anisotropic '
                 'volume (may not be in the center of the head).',
    'mni_tal': 'MNI template in Talairach coordinates',
    'fs_tal': 'Freesurfer template in Talairach coordinates',
    'ras': 'RAS means that the first dimension (X) points towards '
           'the right hand side of the head, the second dimension (Y) '
           'points towards the Anterior aspect of the head, and the '
           'third dimension (Z) points towards the top of the head.',
}

CHANNELS_TYPE_MNE_BIDS = {
    "eeg": "EEG",
    "misc": "MISC",
    "stim": "TRIG",
    "emg": "EMG",
    "ecog": "ECOG",
    "seeg": "SEEG",
    "eog": "EOG",
    "ecg": "ECG",
    "meggradaxial": "MEGGRADAXIAL",
    "megmag": "MEGMAG",
    "megrefgradaxial": "MEGREFGRADAXIAL",
    "meggradplanar": "MEGGRADPLANAR",
    "megrefmag": "MEGREFMAG"
    }

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


# mapping subject information back to mne-python
# XXX: MNE currently only handles R/L,
# follow https://github.com/mne-tools/mne-python/issues/7347
def _convert_hand_options(key, fro, to):
    if fro == 'bids' and to == 'mne':
        hand_options = {'n/a': 0, 'R': 1, 'L': 2, 'A': 3}
    elif fro == 'mne' and to == 'bids':
        hand_options = {0: 'n/a', 1: 'R', 2: 'L', 3: 'A'}
    else:
        raise RuntimeError("fro value {} and to value {} are not "
                           "accepted. Use 'mne', or 'bids'.".format(fro, to))
    return hand_options.get(key, None)


def _convert_sex_options(key, fro, to):
    if fro == 'bids' and to == 'mne':
        sex_options = {'n/a': 0, 'M': 1, 'F': 2}
    elif fro == 'mne' and to == 'bids':
        sex_options = {0: 'n/a', 1: 'M', 2: 'F'}
    else:
        raise RuntimeError("fro value {} and to value {} are not "
                           "accepted. Use 'mne', or 'bids'.".format(fro, to))
    return sex_options.get(key, None)
