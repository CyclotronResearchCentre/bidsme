###############################################################################
# _EDF.py provides additional parameters for EDF classes that uses mne library
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

metafields = {
        "Unknown": {
            # "PowerLineFrequency": ("<line_freq>", None),
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
