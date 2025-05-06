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
import re

from typing import Union, List

from bidsme.Modules import baseModule
from bidsme.tools import tools

logger = logging.getLogger(__name__)


def Convert3Dto4D(outfolder: str,
                  recording: Union[baseModule, List[str], None],
                  skip: int = 0, keep: int = 0, TR=None,
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
        and where all images will be searched
    recording: Modules.baseModule, list[str], None
        recording object to concat, OR explicit list of files
        to concat, OR directory with .nii(.gz) files to concat
        in case of directory, files will be sorted aplphabetically,
        otherwise the order of files will be unchanged
    skip: int
        number of files to exclude from convertion, excluded
        files will be still removed
    keep: int
        maximum number of files to merge
    TR: float or None
        If specified, will add repitition time as axis/last
        dimention. For default 4th dimention (axis=None) unit
        is miliseconds, overwise mm.
        see https://nipy.org/nibabel/nibabel_images.html
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
    if recording is None:
        f_list = _select_files_scandir(outfolder)
    elif isinstance(recording, baseModule):
        f_list = _select_files_list(outfolder, recording.files)
    elif isinstance(recording, list):
        f_list = _select_files_list(outfolder, recording)

    f_list = f_list[skip:]
    if keep > 0:
        f_list = f_list[:keep]

    if len(f_list) == 0:
        logger.warning("No files to concat")
        return ""

    if len(f_list) == 1:
        # Only one file, no need of concatenation
        return f_list[0]

    imgs = [nibabel.load(f) for f in f_list]
    slope = imgs[0].dataobj.slope
    inter = imgs[0].dataobj.inter
    dtype = imgs[0].get_data_dtype()
    do_manual_scale = True

    for img in imgs[1:]:
        if slope != img.dataobj.slope or inter != img.dataobj.inter \
           or dtype != img.get_data_dtype():
            logger.warning('Concatenation of images of different scale '
                           'or dtypes. Will recalculate scale for all files.')
            do_manual_scale = False
            break

    img = nibabel.funcs.concat_images(imgs,
                                      check_affines=check_affines,
                                      axis=axis)
    if do_manual_scale:
        data = img.dataobj[:]
        if inter is not None:
            data -= inter
        if slope is not None:
            data /= slope
        img.header.set_slope_inter(slope, inter)
        img.set_data_dtype(dtype)

    if TR is not None:
        zooms = list(img.header.get_zooms())
        if axis is None:
            zooms[-1] = TR
        else:
            zooms[axis] = TR
        img.header.set_zooms(zooms)

    img.to_filename(f_list[0])

    for file in f_list[1:]:
        os.remove(file)

        aux_file = tools.change_ext(file, "json")
        if os.path.isfile(aux_file):
            os.remove(aux_file)

    return f_list[0]


def _select_files_scandir(outfolder):
    # Generating file list from folder content
    pattern = re.compile(r"[^.]*\.nii(\.gz)?")
    f_list = [os.path.join(outfolder, f.name)
              for f in os.scandir(outfolder)
              if f.is_file()
              and pattern.fullmatch(f.name)]
    f_list.sort()
    return f_list


def _select_files_list(outfolder, f_list):
    f_list = [os.path.join(outfolder, file)
              for file in f_list
              ]
    f_list = [file for file in f_list
              if os.path.exists(file)]
    return f_list
