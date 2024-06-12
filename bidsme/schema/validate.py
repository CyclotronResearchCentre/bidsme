###############################################################################
# validate.py contains functions to test and validate data formats defined in
# BIDSschema
###############################################################################
# Copyright (c) 2019-2020, University of Liège
# Author: Nikita Beliy
# Owner: Liege University https://www.uliege.be
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
import logging

from . import functs

logger = logging.getLogger(__name__)


def validate_value(item, value, formats):

    msg = ""
    if "anyOf" in item:
        for sub_item in item["anyOf"]:
            msg = validate_value(sub_item, value, formats)
            if not msg:
                return ""

        msg = ("'{}' failed for all in {}"
               .format(value, item["anyOf"]))
        return msg

    # Testing type
    test = types.get(item["type"], None)

    if test is None:
        raise KeyError("Type {} not defined".format(item["type"]))

    if item["type"] in ("object", "array"):
        return test(item, value, formats)

    if not test(item, value):
        msg = ("'{}' not of type {}".format(value, item["type"]))
        return msg

    # Testing format
    if "format" in item:
        if item["format"] not in formats:
            raise KeyError("Formats dictionary do not contain entry '{}'"
                           .format(item["format"]))
        fmt = formats[item["format"]]
        msg = functs.test_format(value, fmt)

    if msg:
        return msg

    # Testing enum
    if "enum" in item:
        if value not in item["enum"]:
            msg = ("'{}' not in {}"
                   .format(value, item["enum"]))

    return msg


def test_array(item, value, formats):
    if not isinstance(value, list):
        return "Not a list"

    if "minItems" in item:
        if len(value) < item["minItems"]:
            return "Number of elements below {}".format(item["minItems"])

    if "maxItems" in item:
        if len(value) > item["maxItems"]:
            return "Number of elements above {}".format(item["maxItems"])

    if "items" in item:
        for i, v in enumerate(value):
            msg = validate_value(item["items"], v, formats)
            if msg:
                return "Failed for element {}: {}".format(i, msg)

    return ""


def test_object(item, value, formats):
    if not isinstance(value, dict):
        return "Not an object"

    if "additionalProperties" in item:
        for key, val in value.items():
            msg = validate_value(item["additionalProperties"], val, formats)
            if msg:
                return "Failed for element {}: {}".format(key, msg)
    return ""


types = {"boolean": functs.test_boolean,
         "integer": functs.test_integer,
         "number": functs.test_number,
         "string": functs.test_string,
         "array": test_array,
         "object": test_object,
         }
