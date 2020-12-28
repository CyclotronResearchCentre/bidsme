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

from tools.tools import check_type

logger = logging.getLogger(__name__)


class Run(object):
    __slots__ = [
            "_modality",     # modality associeted with this run
            "_model",        # model (set of entities and json)
            "attribute",     # dictionary of attr:regexp
            "entity",        # dictionary for run entities
            "json",          # dictionary for json fields
            "_suffix",       # suffix associated with run
            "_bk_modality",  # copy of self old values
            "_bk_model",     # copy of self old values
            "_bk_attribute",
            "_bk_entity",
            "_bk_suffix",
            "_bk_json",
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
        self._bk_modality = None
        self._bk_model = None
        self._bk_attribute = dict()
        self._bk_entity = dict()
        self._bk_suffix = None
        self._bk_json = dict()
        self.writable = True
        self.template = False
        self.checked = False
        self.example = example

        self.provenance = provenance
        self._modality = check_type("modality", str, modality)
        self._model = self._modality
        self._suffix = check_type("suffix", str, suffix)
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
        Sets Modality. The old (unmodified) value is backuped
        """
        if self._bk_modality is None:
            self._bk_modality = self._modality
        self._modality = value

    def restore_modality(self) -> None:
        """
        Restore old (unmodified) modality
        """
        if self._bk_modality is not None:
            self._modality = self._bk_modality
            self._bk_modality = None

    @property
    def model(self) -> str:
        """
        Return Model
        """
        return self._model

    @model.setter
    def model(self, value: str) -> None:
        """
        Sets Modality. The old (unmodified) value is backuped
        """
        if self._bk_model is None:
            self._bk_model = self._model
        self._model = value

    def restore_model(self) -> None:
        """
        Restore old (unmodified) modality
        """
        if self._bk_model is not None:
            self._model = self._bk_model
            self._bk_model = None

    @property
    def suffix(self) -> str:
        """
        Return Suffix
        """
        return self._suffix

    @suffix.setter
    def suffix(self, value: str) -> None:
        """
        Sets new suffix. The old (unmodified) value is backuped
        """
        if self._bk_suffix is None:
            self._bk_suffix = self._suffix
        self.suffix = value

    def restore_suffix(self) -> None:
        """
        Restore old (unmodified) suffix
        """
        if self._bk_suffix is not None:
            self._suffix = self._bk_suffix
            self._bk_suffix = None

    def set_attribute(self, attr: str, val: object) -> None:
        """
        Sets attribute value. Old (unmodified) value is backuped

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
            if self.attribute[attr] == val:
                return

            if attr not in self._bk_attribute:
                self._bk_attribute[attr] = self.attribute[attr]

                self.attribute[attr] = val
            return

        else:
            if val == "":
                return
            self.attribute[attr] = val
            if attr not in self._bk_attribute:
                self._bk_attribute[attr] = None

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

            if attr not in self._bk_entity:
                self._bk_entity[attr] = self.entity[attr]

            if val:
                self.entity[attr] = val
            else:
                self.entity.remove(attr)
            return

        else:
            if val == "":
                return
            self.entity[attr] = val
            if attr not in self._bk_entity:
                self._bk_entity[attr] = None

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
            if self.json[attr] == val:
                return

            if attr not in self._bk_json:
                self._bk_json[attr] = self.json[attr]

            if val:
                self.json[attr] = val
            else:
                self.json.remove(attr)
            return

        else:
            if val == "":
                return
            self.json[attr] = val
            if attr not in self._bk_json:
                self._bk_json[attr] = None

    def restore_attribute(self, attr: str) -> None:
        """
        Restore old value of given attribute.
        New value is lost

        Parameters:
        -----------
        attr: str
            name of attribute to restore
        """
        self.__restore_val(attr,
                           self.attribute,
                           self._bk_attribute)

    def restore_attributes(self):
        """
        Restore all attributes to old values.
        New values and new attributes are lost
        """
        for attr in self.attribute:
            self.__restore_val(attr,
                               self.attribute,
                               self._bk_attribute)

    def restore_entity(self, attr: str) -> None:
        """
        Restore old value for given entity.
        New value is lost.
        """
        self.__restore_val(attr,
                           self.entity,
                           self._bk_entity)

    def restore_entities(self) -> None:
        """
        Restore old values for all entities.
        New values and new entities are lost.
        """
        for attr in self.entity:
            self.__restore_val(attr,
                               self.entity,
                               self._bk_entity)

    def restore_json_field(self, attr: str) -> None:
        """
        Restore old value for json field.
        New value is lost
        """
        self.__restore_val(attr,
                           self.json,
                           self._bk_json)

    def restore_json(self) -> None:
        """
        Restore old values for all json fields.
        New values and new fields are lost.
        """
        for attr in self.json:
            self.__restore_val(attr,
                               self.json,
                               self._bk_json)

    def restore(self) -> None:
        """
        Restores old values for modality, suffix,
        attributesm entities and json fields
        """
        self.restore_modality()
        self.restore_model()
        self.restore_suffix()
        self.restore_attributes()
        self.restore_entities()
        self.restore_json()

    def save(self) -> None:
        """
        Saves all current values, old values
        are lost
        """
        self._bk_modality = None
        self._bk_model = None
        self._bk_attribute = dict()
        self._bk_entity = dict()
        self._bk_json = dict()
        self._bk_suffix = None

    def __restore_val(self, attr: str, dest: dict, source: dict) -> None:
        """
        Restore old value from given dictionary.

        Parameters:
        -----------
        attr: str
            name of field to restore
        dest: dict
            dictionary where restore value
        source: dict
            dictionary from which retrieve values
        """
        if attr not in source:
            return
        if source[attr] is None:
            if attr in dest:
                dest.remove(attr)
            return
        dest[attr] = source.pop(attr)

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
        if self.model != self.modality:
            d['model'] = self.model
        d["suffix"] = self.suffix
        d["attributes"] = {k: v for k, v in self.attribute.items()
                           if empty_attributes or v is not None
                           }
        d["bids"] = self.entity
        d["json"] = self.json

        return d

    def genEntities(self, entities: list):
        """
        Completes the existing entities by entities from list
        All added values will be set to None

        Parameters
        ----------
        entities: list
            list of strings with names of entities to add
        """
        for ent in entities:
            if ent not in self.entity:
                self.entity[ent] = None
