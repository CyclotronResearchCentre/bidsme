###############################################################################
# parcing.py contains functions to parceand test selectors from BIDSschema
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
import operator
import re
import logging

from copy import deepcopy
from bidsschematools import expressions

from . import functs

logger = logging.getLogger(__name__)

key_words = {"null": None,
             "true": True,
             "false": False}

functions = {
    "intersects": functs.intersects,
    "match": functs.match
        }

operators = {
    "||": operator.or_,
    "&&": operator.and_,
    "!": operator.not_,
    "==": operator.eq,
    "!=": operator.ne,
    "<": operator.lt,
    "<=": operator.le,
    ">": operator.gt,
    ">=": operator.ge,
    "in": functs.in_,
    "+": operator.add,
    "-": operator.sub,
    "*": operator.mul,
    "/": operator.truediv,
    "**": operator.pow
        }


def test_all_selectors(selectors, inputs, skip=""):
    for sel in selectors:
        if skip and re.search(skip, sel):
            logger.debug("Condition {} skipped".format(sel))
            continue
        try:
            res = test_selector(sel, inputs)
        except Exception as err:
            logger.error("Error: {} in condition '{}'"
                         .format(err, sel))
            res = False
        if not res:
            logger.debug("Condition {} failed".format(sel))
            return False
    return True


def test_selector(selector, inputs):
    inputs = deepcopy(inputs)
    inputs.update(key_words)
    res = resolve(expressions.parse(selector), inputs)
    return bool(res)


def resolve(selector, inputs):
    if isinstance(selector, str):
        if selector.startswith("'") or selector.startswith("\""):
            return selector.strip("\"'")
        if selector in inputs:
            return inputs[selector]
        raise KeyError("'{}' not in inputs"
                       .format(selector))
    if isinstance(selector, expressions.BinOp):
        return resBinOp(selector, inputs)
    if isinstance(selector, expressions.RightOp):
        return resRightOp(selector, inputs)
    if isinstance(selector, expressions.Function):
        return resFunction(selector, inputs)
    if isinstance(selector, expressions.Element):
        return resElement(selector, inputs)
    if isinstance(selector, expressions.Property):
        return resProperty(selector, inputs)
    if isinstance(selector, expressions.Array):
        return resArray(selector, inputs)
    if isinstance(selector, expressions.Object):
        return resObject(selector, inputs)
    if isinstance(selector, expressions.ASTNode):
        raise TypeError("Can't resolve type {}"
                        .format(type(selector)))
    return selector


def resBinOp(selector, inputs):
    lh = resolve(selector.lh, inputs)
    rh = resolve(selector.rh, inputs)

    op = operators.get(selector.op, None)
    if op:
        return op(lh, rh)
    else:
        raise KeyError("Can't interpret operator '{}' in {}"
                       .format(selector.op, selector))


def resRightOp(selector, inputs):
    rh = resolve(selector.rh, inputs)

    op = operators.get(selector.op, None)
    if op:
        return op(rh)
    else:
        raise KeyError("Can't interpret operator '{}' in {}"
                       .format(selector.op, selector))


def resFunction(selector, inputs):
    args = []
    for arg in selector.args:
        args.append(resolve(arg, inputs))

    fun = functions.get(selector.name, None)
    if fun:
        return fun(*args)
    else:
        raise KeyError("Can't interpret function '{}' in {}"
                       .format(selector.name, selector))


def resArray(selector, inputs):
    res = []
    for el in selector.elements:
        res.append(resolve(el, inputs))
    return res


def resProperty(selector, inputs):
    obj = resolve(selector.name, inputs)
    if not isinstance(obj, dict):
        raise TypeError("Can't interpret '{}' as dictionary"
                        .format(selector.name))
    return obj.get(selector.field)


def resElement(selector, inputs):
    array = resolve(selector.name, inputs)
    index = resolve(selector.index, inputs)
    return array[index]


def resObject(selector, inputs):
    raise NotImplementedError("class Object(ASTNode) not implemented")
