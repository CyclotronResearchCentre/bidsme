###############################################################################
# yaml.py defines YAML library interface
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


import ruamel.yaml
# from ruamel.yaml import YAML


yaml = ruamel.yaml.YAML()
yaml.indent(mapping=2, sequence=4, offset=2)
yaml.preserve_quotes = True
# yaml.default_style = "'"


def my_represent_none(self, data):
    return self.represent_scalar(u'tag:yaml.org,2002:null', u'~')


def my_represent_str(self, data):
    data = data.encode('unicode_escape').decode()
    return self.represent_str("'" + data + "'")


yaml.representer.add_representer(type(None), my_represent_none)
# yaml.representer.add_representer(str, my_represent_str)
