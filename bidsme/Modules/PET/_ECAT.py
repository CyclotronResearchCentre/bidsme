###############################################################################
# _ECAT.py provides additional parameters for ECAT class
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
            "Unit": ("<data_units>", None),
            "TracerName": ("<radiopharmaceutical>", None),
            "TracerRadionuclide": ("<isotope_name>", None),
            "InjectedRadioactivity": ("<dosage>", None),
            "ScanStart": ("<time:scan_start_time>", None),
            "InjectionStart": ("<time:dose_start_time>", None),
            "AcquisitionMode": ("<acquisition_mode>", None),
            "ReconMatrixSize": [("<0:x_dimension>", None),
                                ("<0:y_dimension>", None),
                                ("<0:z_dimension>", None)],
            "ImageVoxelSize": [("<0:x_resolution>", None),
                               ("<0:y_resolution>", None),
                               ("<0:z_resolution>", None)],
            "ScanDate": ("<date:scan_start_time>", None),
            "FrameTimesStart": ("<FramesStart>", None),
            "FrameTimesStartUnit": ("s", None),
            "FrameDuration": ("<FramesDuration>", None),
            "FrameDurationStartUnit": ("s", None),
            },
        }
