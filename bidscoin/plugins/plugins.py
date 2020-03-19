#############################################################################
# plugins defines a structure to define and use for plugin files
#############################################################################
# Copyright (c) 2018-2019, University of Liège
# Author: Nikita Beliy
# Owner: Liege University https://www.uliege.be
# Version: 0.77r1
# Maintainer: Nikita Beliy
# Email: Nikita.Beliy@uliege.be
# Status: developpement
#############################################################################
# This file is part of eegBidsCreator
# eegBidsCreator is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
# eegBidsCreator is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with eegBidsCreator.  If not, see <https://www.gnu.org/licenses/>.
############################################################################

import sys
import os
import importlib.util
import logging

from tools.tools import check_type

from . import exceptions
from .entry_points import entry_points

logger = logging.getLogger(__name__)

file = ""
active_plugins = dict()


def ImportPlugins(plugin_file):
    """
    Import aviable plugins from given file

    Parameters
    ----------
    plugin_file : str
        path to the plugin file

    Returns
    -------
    int
        number of imported plugin functions

    Raises
    ------
    exceptions.PluginNotfound :
        if plugin file not found
    exceptions.PluginModuleNotFound :
        if inable to load plugin module
    """
    plugin_file = check_type("plugin_file", str, plugin_file)
    if plugin_file == "":
        return 0

    global file

    file = str(plugin_file)

    if not os.path.isfile(file):
        raise exceptions.PluginNotFoundError("Plug-in file {} not found"
                                             .format(file))

    pl_name = os.path.splitext(os.path.basename(file))[0]
    logger.info("Loading module {} from {}".format(pl_name, file))
    spec = importlib.util.spec_from_file_location(pl_name, file)
    if spec is None:
        raise exceptions.PluginModuleNotFoundError(
                "Unable to load module {} from {}"
                .format(pl_name, file)
                )
    itertools = importlib.util.module_from_spec(spec)
    # Adding plugin directory to path
    # Need better solution
    sys.path.append(os.path.dirname(file))
    #
    spec.loader.exec_module(itertools)
    f_list = dir(itertools)
    for ep in entry_points:
        if ep in f_list and callable(getattr(itertools, ep)):
            logger.debug("Entry point {} found".format(ep))
            active_plugins[ep] = getattr(itertools, ep)
    if len(active_plugins) == 0:
        logger.warning("Plugin {} loaded but "
                       "no compatible functions found".format(pl_name))
    return len(active_plugins)


def InitPlugin(**cfi_params):
    """
    Initialize the plugin by calling InitEP function with command line (args)
    and configuration file (kwargs) arguments

    Parameters
    ----------
    cfi_params: dict
        dictionary of parameters from configuration file passed to plugin
    """
    if "InitEP" not in active_plugins:
        return
    return RunPlugin("InitEP", **cfi_params)


def RunPlugin(entry, *args, **kwargs) -> int:
    """
    Executes a given function from plugin, recovers the exit code of plugin
    and transforms it into corresponding exception.

    Parameters
    ----------
    entry : str
        the name of plugin function in entry_points list
    args : list
        list of unamed (positional) arguments passed to plugin
    kwargs : dict
        list of named arguments passed to plugin

    Raises
    ------
    TypeError :
        if some of parameters are of incorrect type

    Returns
    -------
    int:
        plugin exit code, can be 0 or < 0. Positive
        exit codes will raise an exception
    """
    if entry not in active_plugins:
        return 0
    try:
        if kwargs:
            result = active_plugins[entry](*args, **kwargs)
        else:
            result = active_plugins[entry](*args)
    except exceptions.PluginError:
        raise
    except Exception as e:
        raise entry_points[entry]("{}: {}".format(type(e).__name__, e))\
                .with_traceback(sys.exc_info()[2])
    if result is None:
        result = 0

    if result > 0:
        e = entry_points[entry]("Plugin {} returned code {}"
                                .format(entry, result))
        e.code = result
        raise e
    return result
