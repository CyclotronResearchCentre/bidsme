###############################################################################
# functs.py implements operators and small tests for datatypes for validation
# of fields
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
import re

classes = {
    "NoneType": "null",
    "list": "array",
    "int": "number",
    "dict": "object",
    "bool": "boolean"
        }


def in_(val, li):
    if hasattr(li, '__iter__'):
        return val in li
    else:
        return False


def intersects(l_list, r_list):
    if hasattr(l_list, '__iter__') and hasattr(r_list, '__iter__'):
        return [el for el in l_list if el in r_list]
    return False


def match(string, pattern):
    return bool(re.fullmatch(pattern, string))


def type(item):
    if item is None:
        return "null"
    if isinstance(item, list):
        return "array"
    if isinstance(item, dict):
        return "object"
    return "unknown"


def test_boolean(item, value):
    return isinstance(value, bool)


def test_number(item, value):
    if not isinstance(value, (int, float)):
        return False
    return test_limit(item, value)


def test_integer(item, value):
    if not isinstance(value, int):
        return False
    return test_limit(item, value)


def test_string(item, value):
    return isinstance(value, str)


def test_limit(item, value):
    if "minimum" in item:
        if value < item["minimum"]:
            return False

    if "maximum" in item:
        if value > item["maximum"]:
            return False

    if "exclusiveMinimum" in item:
        if value <= item["exclusiveMinimum"]:
            return False

    if "exclusiveMaximum" in item:
        if value >= item["exclusiveMaximum"]:
            return False
    return True


def test_format(value, fmt):

    if "pattern" not in fmt:
        return ""

    pattern = fmt["pattern"]
    res = re.fullmatch(pattern, str(value))

    if res:
        return ""

    return ("'{}' do not match format {} ({})"
            .format(value, fmt["display_name"], fmt["pattern"]))
