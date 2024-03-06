###############################################################################
# Nibabel.py contains tools, that can be used in user plugins
# these tools do require nibabel module installed
###############################################################################
# Copyright (c) 2019-2020, University of Liège
# Author: Nikita Beliy
# Owner: Liege University https://www.uliege.be
# Credits: [Marcel Zwiers]
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

import os
import logging
import nibabel

from bidsme.Modules import baseModule
from bidsme.tools import tools

logger = logging.getLogger(__name__)


def Convert3Dto4D(outfolder: str,
                  recording: baseModule,
                  skip: int = 0, keep: int = 0,
                  check_affines: bool = True, axis: int = None) -> str:
    """
    Concat nii images from recording into one 4D image, using
    nibabel.funcs.concat_images function. The scaling parameters
    of Nifti will be preserved if all files has the same slope and
    intercept, otherwise, the scaling will be recalculated.

    It will work only on single file nii images, not with hdr/img pair.

    If number of files in recording is too small (0, 1, <=skip)
    a warning will be shown and no concatination will be performed

    Original 3D images are removed.

    This function is intended to be run in SequenceEndEP, in order
    to avoid conflicts due to file removal

    Resulting file will be named as first file used to concatenation
    in order to conserve naming in case of use of header dumps

    Parameters:
    -----------
    outfolder: str
        path to output folder where data files has been copied
    recording: Modules.baseModule
        recording object to concat
    skip: int
        number of files to exclude from convertion, excluded
        files will be still removed
    keep: int
        maximum number of files to merge
    check_affines: bool
        If True, then check that all the affines for images
        are nearly the same, raising a ValueError otherwise.
        Default is True
    axis: None or int
        If None, concatenates on a new dimension. This requires
        all images to be the same shape. If not None, concatenates
        on the specified dimension. This requires all images
        to be the same shape, except on the specified dimension.

    Returns:
    --------
    str:
        path to merged file

    Example:
    --------
    # In SequenceEndEP, given
    #   recording is BaseModule object
    #   outfolder is the path where files are copied
    if not dry_run:
        Convert3Dto4D(outfolder, recording)
    """

    # Generating file list
    if len(recording.files) <= 1:
        logger.warning("No files to concat")
        return
    f_list = recording.files[skip:]
    if keep > 0:
        f_list = f_list[:keep]
    if len(f_list) == 0:
        logger.warning("No files to concat after selection")
        return ""
    f_list = [os.path.join(outfolder, file)
              for file in f_list
              ]
    f_list = [file for file in f_list
              if os.path.exists(file)]

    imgs = [nibabel.load(f) for f in f_list]
    slope = imgs[0].dataobj.slope
    inter = imgs[0].dataobj.inter

    for img in imgs[1:]:
        if slope != img.dataobj.slope or inter != img.dataobj.inter:
            logger.warning('Concatenation of images of different scale. '
                           'Will recalculate scale for all files.')
            slope = None
            inter = None
            break

    img = nibabel.funcs.concat_images(imgs,
                                      check_affines=check_affines,
                                      axis=axis)
    img.header.set_slope_inter(slope, inter)
    img.to_filename(f_list[0])

    for file in f_list[1:]:
        os.remove(file)
        
        aux_file = tools.change_ext(file, "json")
        if os.path.isfile(aux_file):
            os.remove(aux_file)

    return f_list[0]
