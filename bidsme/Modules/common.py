###############################################################################
# common.py provides various common functions to use by Module subclasses
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

from .exceptions import InvalidActionError


def action_value(value: object, action: str) -> object:
    """
    Applies an action defined by prefix to a value,
    retuns the outcome

    Accepted actions:
        "": no action, return value
        int: cast value to int
        float: cast value to float
        str: cast value to string
        format<parameters>: apply python3 formatting
            mini-language to value, {:<parameters>}.format(value)
        scale<int>: apply a 10-based scale to value,
            value ** <int>
        mult<float>: multiply value
        div<float>: divide value
        round<int>: round value to given precision

    Parameters
    ----------
    value:  object
        object to transform
    action: str
        name of action to apply

    Returns
    -------
    object:
        result of an action

    Raises
    ------
    InvalidActionError:
        if action name is invalid
    TypeError:
        if value has invalid type for action
    ValueError:
        if value is invalid for action
    """
    if action == "":
        return value

    # type casting
    if action == "int":
        return int(value)
    if action == "float":
        return float(value)
    if action == "str":
        return str(value)

    # formatting
    if action.startswith("format"):
        f = "{:" + action[len("format"):] + "}"
        return f.format(value)

    # operations
    if action.startswith("scale"):
        if not isinstance(value, int) and not isinstance(value, float):
            raise TypeError("Value must be a numeral")
        exp = int(action[len("scale"):])
        if exp > 0:
            return value * (10 ** exp)
        else:
            return value / (10 ** - exp)
    if action.startswith("mult"):
        if not isinstance(value, int) and not isinstance(value, float):
            raise TypeError("Value must be a numeral")
        par = float(action[len("mult"):])
        return value * par
    if action.startswith("div"):
        if not isinstance(value, int) and not isinstance(value, float):
            raise TypeError("Value must be a numeral")
        par = float(action[len("div"):])
        return value / par
    if action.startswith("round"):
        if not isinstance(value, int) and not isinstance(value, float):
            raise TypeError("Value must be a numeral")
        par = action[len("round"):]
        if par == "":
            return round(value)
        else:
            par = int(par)
            return round(value, par)

    raise InvalidActionError(action)


def retrieveFormDict(field: list, dictionary: dict) -> object:
    """
    retrieves value given by path stored in field from dictionary
    Use if retrieved metadata is stored in standard python dict

    Parameters
    ----------
    field: list
        splitted path to needed value
    dictionary: dict
        dict from which value is retrieved

    Returns
    -------
    object:
        retrieved value
    None:
        if value don't exists in valid path

    Raises
    ------
    KeyError:
        if unable to retrieve
    """
    value = dictionary
    count = 0
    try:
        for f in field:
            count += 1
            if isinstance(value, list):
                value = value[int(f)]
            elif isinstance(value, dict):
                value = value[f]
            else:
                break
    except KeyError as e:
        if count == len(field):
            return None
        raise KeyError("{}: key error {}"
                       .format(field[0:count], e))
    except IndexError as e:
        if count == len(field):
            return None
        raise KeyError("{}: key error {}"
                       .format(field[0:count], f))
    return value
