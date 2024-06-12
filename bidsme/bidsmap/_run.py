###############################################################################
# _run.py defines Run class that manages individual runs from which bidsmap
# is constructed
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


import logging

from collections import OrderedDict

from bidsme.tools.tools import check_type

logger = logging.getLogger(__name__)


class Run(object):
    __slots__ = [
            "_modality",     # modality associeted with this run
            "_model",        # model (set of entities and json)
            "attribute",     # dictionary of attr:regexp
            "entity",        # dictionary for run entities
            "json",          # dictionary for json fields
            "_suffix",       # suffix associated with run
            "provenance",    # file from which run is modelled
            "example",       # bids name from provenance file
            "writable",
            "checked",       # switch if run was confirmed by user
            "template"       # switch if run was extracted from template
            ]

    def __init__(self, *,
                 modality: str = "",
                 attribute: dict = {},
                 entity: OrderedDict = {},
                 json: OrderedDict = {},
                 suffix: str = "",
                 provenance: str = None,
                 example: str = None,
                 ):
        """
        Run class contains all information needed to identify and generate
        the bidsified name. All init parameters must be named.

        Parameters
        ----------
        modality: str
            the modality corresponding to given run
        attribute: dict
            dict of attributes (keys) and values (value) to match
        entity: OrderedDict
            dict of bids fields (keys) and values (value) to
            generate bidsified name
        json: OrderedDict
            dict of json fields (keys) and values (value) to
            fill sidecar json file
        suffix: str
            suffix associated with given run
        provenance: str
            path to the file from which this run was generated
        example: str
            example of bidsified name generated from provenance
            file
        """
        self.writable = True
        self.template = False
        self.checked = False
        self.example = example

        self.provenance = provenance
        self._modality = check_type("modality", str, modality)
        self._suffix = check_type("suffix", str, suffix)
        if self._modality.startswith("__"):
            self._model = self._modality
        else:
            self._model = ":".join([self._modality, self._suffix])
        self.attribute = dict(check_type("attribute", dict, attribute))
        self.entity = OrderedDict(check_type("entity", dict, entity))
        # Checking if values of entity are strings
        for key in self.entity:
            if self.entity[key] is None:
                continue
            if not isinstance(self.entity[key], str):
                logger.warning("Modality {} ({}): bids entity {} value "
                               "is not string. "
                               "May lead to unexpected results."
                               .format(self._modality, self.provenance,
                                       key))
                self.entity[key] = str(self.entity[key])
        self.json = OrderedDict(check_type("json", dict, json))

    def __bool__(self) -> bool:
        """
        Return True if suffix is defined
        """
        if self._suffix == "":
            return False
        return True

    @property
    def modality(self) -> str:
        """
        Return Modality
        """
        return self._modality

    @modality.setter
    def modality(self, value: str) -> None:
        """
        Sets Modality.
        """
        self._modality = value

    @property
    def model(self) -> str:
        """
        Return Model
        """
        return self._model

    @model.setter
    def model(self, value: str) -> None:
        """
        Sets model.
        """
        self._model = value

    @property
    def suffix(self) -> str:
        """
        Return Suffix
        """
        return self._suffix

    @suffix.setter
    def suffix(self, value: str) -> None:
        """
        Sets new suffix.
        """
        self.suffix = value

    def set_attribute(self, attr: str, val: object) -> None:
        """
        Sets attribute value.

        Parameters
        ----------
        attr: str
            name of attribute to set
        value: object
            value to match given attribute
        """
        if isinstance(val, str):
            val = val.encode('unicode_escape').decode()
        attr = check_type("attr", str, attr)
        if attr in self.attribute:
            self.attribute[attr] = val
        else:
            if val == "":
                return
            self.attribute[attr] = val

    def set_entity(self, ent: str, val: str) -> None:
        """
        Sets entity value. Old (unmodified) value is backuped

        Parameters
        ----------
        ent: str
            name of entity to set
        val: str
            value of entity
        """
        val = check_type("val", str, val)
        attr = check_type("ent", str, ent)

        if attr in self.entity:
            if self.entity[attr] == val:
                return
            if val:
                self.entity[attr] = val
            else:
                self.entity.remove(attr)
            return
        else:
            if val == "":
                return
            self.entity[attr] = val

    def set_json_field(self, field: str, val: object) -> None:
        """
        Sets the json field value. The old (unmodified) value is backuped

        Parameters:
        -----------
        field: str
            name of field to set
        val: object
            value to set
        """
        if isinstance(val, str):
            val = val.encode('unicode_escape').decode()
        attr = check_type("field", str, field)

        if attr in self.json:
            if val:
                self.json[attr] = val
            else:
                self.json.remove(attr)
            return
        else:
            if val == "":
                return
            self.json[attr] = val

    def dump(self, empty_attributes: bool = True) -> dict:
        """
        Dumps run into a dictionary

        Parameters:
        -----------
        empty_attributes: bool
            if True, the void and empty attributes are also dumped,
            if False, viod values are ignored
        """
        d = dict()
        d["provenance"] = self.provenance
        if self.example:
            d["example"] = self.example
        if self.template:
            d["template"] = self.template
        d["checked"] = self.checked
        d['model'] = self.model
        d["suffix"] = self.suffix
        d["attributes"] = {k: v for k, v in self.attribute.items()
                           if empty_attributes or v is not None
                           }
        d["bids"] = self.entity
        d["json"] = self.json

        return d

    def genEntities(self, entities: OrderedDict):
        """
        Completes the existing entities by entities from list
        All added values will be set to None

        Parameters
        ----------
        entities: dict
            list of entities from schema and corresponding
            requirement label
        """
        # Copying entities from schema
        # entities.update(self.entity)
        for ent, val in self.entity.items():
            entities[ent] = val
        self.entity = entities
