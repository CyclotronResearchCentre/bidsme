###############################################################################
# BIDSschema.py contains class that loads BIDS schema, creates models for given
# sullfix and datatype, and performs validation of bidsified files
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
import os
import logging

from typing import Union
from collections import OrderedDict
from enum import IntEnum
from copy import deepcopy

from bidsschematools.types import Namespace
from bidsschematools import schema as bst

from .parcing import test_all_selectors

from .validate import validate_value

logger = logging.getLogger(__name__)

# Enum type for parsing requirements levels
requirement = IntEnum('req',
                      ["required", "recommended",
                       "optional", "deprecated"],
                      start=0)

# Corresponding placeholders
req_values = ["<<placeholder>>", "", None, None]

# List of datatypes (coinciding with schema file names) for
# given modality, task and photo will be added automatically
modalities = {"mri": ["anat", "dwi", "fmap", "func", "perf", "asl"],
              "pet": ["pet"], "beh": ["beh"],
              "eeg": ["eeg", "channels"],
              "ieeg": ["ieeg", "channels"],
              "meg": ["meg", "channels"], "nirs": ["nirs", "channels"],
              "micr": ["micr"], "motion": ["motion", "channels"],
              "mrs": ["mrs"]
              }


def get_modality(dt: str) -> Union[str, None]:
    """
    Returns modality assosiated with provided datatype

    Parameters:
    -----------
    dt: str
        datatype for wich modality must be founs

    Returns:
    --------
    Union[str, None]
    """
    for mod in modalities:
        if dt in modalities[mod]:
            return mod
    return None


class BIDSschema(object):

    _schema = {}
    # Shortcuts to definitions
    _entities_order = []
    _entities = {}
    _metadata = {}
    _formats = {}

    __slots__ = ["entities", "sidecar",
                 "modality", "data_types",
                 "ent_rules", "meta_rules"]

    # entities and sidecar fields with level greater than this
    # value (deprecated) will be ignored
    deprecated = requirement["deprecated"]

    def __init__(self, modality: str, datatypes: Union[list, None] = None):
        """
        Class managing BIDS schema for given modality.

        It will load rules from <modality>.yaml and similary from
        list in datatypes. If datatypes is None, the default list,
        assosiated with modality will be used.

        Rules from task.yaml, photo.yaml and continious.yaml and
        entities_rules.yaml will be always loaded.

        Parameters:
        -----------
        modality: str
            modality to load rules for
        datatypes: Union[list, None], optional
            list of datatypes to be associated with modality. If
            not provided, default list will be used.
        """
        self.entities = dict()
        self.sidecar = dict()

        if not self._schema:
            logger.warning("No schema loaded.")
            self.load_schema()

        self.modality = modality
        if datatypes is None:
            datatypes = modalities.get(modality, [])
            datatypes.append("task")
            datatypes.append("photo")
        self.data_types = [dt for dt in datatypes
                           if dt != modality]

        self.ent_rules = OrderedDict()
        for dt in [self.modality] + self.data_types:
            rule = self._schema.rules.files.raw.get(dt)
            if rule:
                self.ent_rules[dt] = rule

        self.meta_rules = OrderedDict()
        for dt in [self.modality] + self.data_types:
            rule = self._schema.rules.sidecars.get(dt)
            if rule:
                self.meta_rules[dt] = rule

        # Adding generic rules
        self.meta_rules["continuous"] = self._schema.rules.sidecars.continuous
        self.meta_rules["entity_rules"] = \
            self._schema.rules.sidecars.entity_rules

    def get_entities(self, model: str) -> OrderedDict:
        """
        Retrieves the entities defined for given model in order
        defined by loaded schema, in form of ordered dictionary
        with values corresponding to the placeholder depending
        on the requirement level.

        Entities that are defined for schema, but not appearing
        in schema's entities list will be appended to the end
        of dictionary.

        Entities that are deprecated are ignored.

        Parameters:
        -----------
        model: str
            model name for which entities will be retrieved

        Returns:
        --------
        OrderedDict
        """
        res = OrderedDict()
        if model == "<none>":
            return res

        entities = {}

        inputs = self._get_models(model)

        if isinstance(inputs, dict):
            rule = self.get_ent_rule(inputs["datatype"], inputs["suffix"],
                                     rulesets=self.ent_rules)
        else:
            rule = self.get_ent_rule(model, rulesets=self.ent_rules)

        if not rule:
            logger.error("Schema {}: no matching rule for '{}'"
                         .format(self.modality, model))
            return res

        entities = rule.entities

        # Reordering entities
        for ent in self._entities_order:
            if ent not in entities:
                continue
            level, _ = self._get_requirement_from_level(entities[ent])
            level = req_values[level]
            ent_name = self._entities[ent]["name"]
            res[ent_name] = level

        return res

    def get_sidecar(self,
                    datatype: Union[str, None] = None,
                    suffix: Union[str, None] = None,
                    extension: Union[str, None] = None,
                    entities: dict = {},
                    sidecar: dict = {},
                    modalities: list = [],
                    datatypes: list = [],
                    ) -> dict:
        """
        Retrieves the sidecar fields defined for provided parameters.
        Retrieved metafields will be placed into dictionary as keys,
        with values being placeholders for corresponding requirement
        level.

        Fields that are deprecated are ignored.

        If no extension provided, all selectors with suffix will be
        assumed to be satisfied.

        Parameters:
        -----------
        datatype: Union[str, None], optional
        suffix: Union[str, None], optional
        extension: Union[str, None], optional
            if not provided (None), the selectors containing suffix
            will be accepted.
        entities: dict, optional
            dictionary of entities for selectors. Keys with empty
            values are ignored. So task: None will not trigger
            'task in entities' selector.
        sidecar: dict, optional
            dictionary of sidecar for selectors. Keys with empty
            values are ignored.
        modalities: list, optional
            list of modalities in the cuttent dataset.
            For selectors 'pet in dataset.modalities'
        datatypes: list, optional
            list of datatypes in current session.
            For selectors 'anat in dataset.datatypes'

        Returns:
        --------
        dict
        """
        res = {}
        logger.debug("Scanning sidecar rules for {}:{}"
                     .format(datatype, suffix))
        if extension is None:
            skip = "extension"
        else:
            skip = ""

        # Removing empty valuse from entities and sidecars
        entities = self._clean_keys(entities)
        sidecar = self._clean_keys(sidecar)

        rules = self.get_sidecar_rule(self.meta_rules, skip,
                                      modality=self.modality,
                                      datatype=datatype,
                                      suffix=suffix,
                                      extension=extension,
                                      entities=entities,
                                      entity=entities,
                                      sidecar=sidecar,
                                      json=sidecar,
                                      dataset={"modalities": [],
                                               "datatypes": []}
                                      )

        for name, rule in rules.items():
            for field, val in rule.fields.items():
                level, _ = self._get_requirement_from_level(val)
                level = req_values[level]
                if field in self._metadata:
                    field = self._metadata[field].name
                res[field] = level
        return res

    @staticmethod
    def split_fname(name: str) -> (dict, str, str):
        """
        Helper function for extracting entities, suffix and
        extension from file name. Input name are assumed to
        follow BIDS specification.

        Parameters:
        -----------
        name: str
            file name to parse

        Returns:
        --------
        (dict, str, str)
            dict of entities in file
            suffix
            extension

        Raises:
        -------
        ValueError:
            If file don't have an extension
        ValueError:
            If some entities don't have values
        """
        name_parts = name.split("_")
        suffix = name_parts[-1]
        res = suffix.split(".", 1)
        ext = ""
        suffix = res[0]
        if len(res) == 2:
            ext = "." + res[1]
        else:
            raise ValueError("File name do not contain extension")

        entities = OrderedDict()
        for ent in name_parts[:-1]:
            res = ent.split("-", 1)
            if len(res) != 2 or res[1] == "":
                raise ValueError("Entity {} has no corresponding value"
                                 .format(res[0]))
                continue
            entities[res[0]] = res[1]
        return (entities, suffix, ext)

    @classmethod
    def validate(self, name: str, sidecar: dict,
                 modalities: list = [],
                 datatypes: list = []) -> bool:
        """
        Validates provided file with it's sidecar by testing
        all rules in loaded BIDS schema.

        All found incompatibilities are logged as errors.

        Parameters:
        -----------
        name, str
            filename with an datatype folder (e.g. anat/sub-123_T1w.nii)
        sidecar: dict
            loaded sidecar for provided file
        modalities: list, optional
            list of modalities in the current dataset
        datatypes: list, optional
            list of datatypes in current dataset

        Returns:
        --------
        bool
            Validation status
        """

        [dt, fname] = os.path.split(name)

        try:
            entities, suffix, ext = self.split_fname(fname)
        except ValueError as e:
            logger.error(e)
            return False

        rule = self.get_ent_rule(dt, suffix)
        if not rule:
            logger.error("No file rule matching datatype '{}' and suffix '{}'"
                         .format(dt, suffix))
            return False

        if ext not in rule.extensions:
            logger.warning("Extension {} not allowed".format(ext))
            logger.info("Allowed extensions: {}".format(rule.extensions))

        res_ent = self.validate_name(entities, rule)

        rules = self.get_sidecar_rule(modality=get_modality(dt),
                                      datatype=dt,
                                      suffix=suffix,
                                      extension=ext,
                                      entities=entities,
                                      entity=entities,
                                      sidecar=sidecar,
                                      json=sidecar,
                                      dataset={"modalities": modalities,
                                               "datatypes": datatypes}
                                      )
        res_sidecar = self.validate_sidecar(sidecar, rules)
        return res_ent and res_sidecar

    @classmethod
    def get_ent_rule(cls, dt: str, suffix: Union[str, None] = None,
                     rulesets: Union[dict, None] = None
                     ) -> Union[Namespace, None]:
        """
        Return first BIDS rule from rulesets matching provided
        datatype and suffix.

        If suffix is None, returns the first rule named <dt>.

        Parameters:
        -----------
        dt: str
            datatype, or rule name (f suffix is None)
        suffix: Union[str, None], optional
            suffix
        rulesets: Union[dict, None], optional
            Dictionary of rules to check. Rules themselves
            must be bidsschematools.types.Namespace. If None,
            loaded rules of current modality will be used.

        Returns:
        --------
        Union[bidsschematools.types.Namespace, None]
            selected rule or None if no matching rule found
        """
        index = ""
        modality = ""
        if rulesets is None:
            rulesets = cls._schema.rules.files.raw

        if suffix is None:
            # No suffix, searching by index
            for mod in rulesets:
                if dt in rulesets[mod]:
                    index = dt
                    modality = mod
                    break
        else:
            for mod in rulesets:
                # Search by (datatype, siffix) pair
                for cat, sub_rule in rulesets[mod].items():
                    if dt not in sub_rule.datatypes:
                        continue
                    if suffix not in sub_rule.suffixes:
                        continue
                    index = cat
                    modality = mod
                    break

        if not index:
            return None

        logger.info("Matched {}/{} rule".format(modality, index))
        return rulesets[modality][index]

    @classmethod
    def get_sidecar_rule(self, ruleset: Union[dict, None] = None,
                         skip: str = "",
                         **inputs) -> dict:
        """
        Returns dictionary of rules matching criteria defined
        in inputs.

        Parameters:
        -----------
        ruleset: Union[dict, None], optional
            dictionary of rules to test, if not defined, all
            rules from rules/sidecars will be checked
        skip: str, optional
            Regexp to skip particular selectors. For ex.
            'extension' will skip all selectors that test
            extension
        **inputs:
            parameters to pass to selectors to test, for ex.
            sidecar={'FlipAngle':90}

        Returns:
        --------
        dict:
            dictionary of matched rules
        """
        if not ruleset:
            ruleset = self._schema.rules.sidecars

        rules = OrderedDict()
        for mod in ruleset:
            for cat, sub_rule in ruleset[mod].items():
                if "selectors" not in sub_rule:
                    continue
                res = True
                rule_name = "{}/{}".format(mod, cat)
                logger.debug("Testing rule {}".format(rule_name))
                res = test_all_selectors(sub_rule.selectors, inputs, skip=skip)
                if res:
                    rules[rule_name] = sub_rule
        return rules

    @classmethod
    def validate_name(self, entities: dict, rule: Namespace) -> bool:
        """
        Tests if dictionary of entities satisfy provided rule.

        It will check for:
            presence of required entities
            format of entities values
            entities order
            presence of non-defined entities

        Found discrepencies will be logged as errors

        Parameters:
        -----------
        entities: dict
            Dictionary of defined entities
        rule: Namespace
            BIDS rule to test, as defined in rules/files/raw

        Returns:
        --------
        bool
        """

        passed = True
        good_order = True

        ent_dict = self._schema.objects.entities
        formats = self._schema.objects.formats

        # Checking entities and corresponding values
        test_order = list(entities)
        entities_order = [ent for ent in self._schema.rules.entities
                          if ent in rule.entities]
        for ref_entity in entities_order:
            if ref_entity in rule.entities:
                req, _ = self._get_requirement_from_level(
                        rule.entities[ref_entity])
                ref_entity = ent_dict[ref_entity]

                # Entity not defined
                if ref_entity.name not in entities:
                    if req == 0:
                        logger.error("Missing required entity {} ({})"
                                     .format(ref_entity.display_name,
                                             ref_entity.name))
                        logger.info(ref_entity.description)
                        passed = False
                    continue

                # Checking format
                test_value = entities.pop(ref_entity.name)
                msg = validate_value(ref_entity, test_value, formats)
                if msg:
                    logger.error("Invalid entity '{}-{}': {}"
                                 .format(ref_entity.name,
                                         test_value,
                                         msg)
                                 )
                    passed = False

                if ref_entity.name != test_order[0]:
                    good_order = False
                test_order.pop(0)

        # Entities out of order
        if not good_order:
            logger.error("Entities do not follow expected order")
            exp_order = [ent_dict[ent].name for ent in entities_order]
            logger.info("Expected order: {}".format(exp_order))
            passed = False

        # Extra entities
        if entities:
            logger.error("Found following extra entities: {}"
                         .format(list(entities)))
            exp_order = [ent_dict[ent].name for ent in entities_order]
            logger.info("Expected entities: {}".format(exp_order))
            passed = False

        return passed

    @classmethod
    def validate_sidecar(self, sidecar: dict, rules: dict):
        """
        Validetes provided sidecar using provided rules.

        Checks for:
            Presence of required fields
            Presence of deprecated fields
            Format of field values
            Format of values of fields that are not defined
                provided rules.

        Discrepencies are logged as errors, except for fields
        that are not defined in rules. These discrepencies are
        reported as warnings.

        Parameters:
        -----------
        sidecar: dict
            dictionary of sidecar metafields
        rules: dict
            dictionary of rules, all rules must be of
            bidsschematools.types.Namespace type

        Returns:
        --------
        bool
        """
        passed = True
        sidecar_extra = deepcopy(sidecar)
        for name, rule in rules.items():
            logger.debug("Testing {}".format(name))
            for field, req in rule.fields.items():
                ref_field = self._metadata[field]
                req, add = self._get_requirement_from_level(req)

                # Field not in sidecar
                if ref_field.name not in sidecar:
                    if req == 0:
                        logger.error("Missing required field {} ({})"
                                     .format(ref_field.display_name,
                                             ref_field.name))
                        logger.info(ref_field.description)
                        if isinstance(field, Namespace) \
                                and "description_addendum" in field:
                            logger.info(field.description_addendum)
                        passed = False
                    continue

                # Checking deprecated
                if req >= self.deprecated:
                    logger.warning("Field '{}' is deprecated"
                                   .format(ref_field.name))

                # Checking format
                if ref_field.name not in sidecar_extra:
                    continue

                test_value = sidecar_extra.pop(ref_field.name)
                msg = validate_value(ref_field, test_value, self._formats)
                if msg:
                    logger.error("Rule {} failed".format(name))
                    logger.error("Invalid field value '{}:{}' -- {}"
                                 .format(ref_field.name,
                                         test_value,
                                         msg)
                                 )
                    logger.info(ref_field.description)
                    passed = False

        # Checking remining fields (not in defined metadata for suffix
        # but defined in metadata dict)
        for field, value in sidecar_extra.items():
            ref_field = self._metadata.get(field, None)
            if ref_field is None:
                logger.warning("Extra field '{}' is not part of BIDS"
                               .format(field))
                continue
            logger.error("Extra field '{}' do not match any rules"
                           .format(ref_field.name))
            msg = validate_value(ref_field, value, self._formats)
            if msg:
                logger.error("Invalid field value '{}:{}' -- {}"
                             .format(ref_field.name, value, msg)
                             )
            logger.info(ref_field.description)
        return passed

    @classmethod
    def load_schema(cls, path: Union[str, None] = None) -> None:
        """
        Loads BIDS schema from path

        Parameters:
        -----------
        path: str, optional
            Path to shchema folder, if None (default),
            schema from bidsschematools is imported
        """
        cls._schema = bst.load_schema(path)
        logger.info("Loaded BIDS schema version {}"
                    .format(cls._schema["bids_version"]))
        cls._entities_order = cls._schema.rules.entities[2:]
        cls._entities = cls._schema.objects.entities
        cls._metadata = cls._schema.objects.metadata
        cls._formats = cls._schema.objects.formats

    # Internal static methods
    @staticmethod
    def _get_requirement_from_level(level: str) -> (int, str):
        """
        Returns level from level string, based on first word
        in the string.

        Parameters:
        -----------
        level: str
            level string to extract

        Returns:
        --------
        (int, str)
            IntEnum elemet corresponding to level
            Associated level addendum string
        """
        add = ""
        if not isinstance(level, str):
            add = level.get("level_addendum", "").strip()
            level = level["level"]
        level = level.replace(",", " ", 1).split(" ", 1)
        val = level[0]
        if len(level) == 2:
            add = level[1].strip()

        return (requirement[val.lower()], add)

    @staticmethod
    def _get_models(model: str) -> Union[list, str]:
        """
        Retrieves generic models associated to passed model.
        Given model "<data_type>:<suffix>", returns:
        {"datatype": <data_type>,
         "suffix": <suffix>}

        If model not splitable by ':', returns model itself

        Parameters:
        -----------
        model: str
            basic model name

        Returns:
        --------
        Union[dict, str]
            Either a dict datatype, suffix or model, depending
            if provided model contains ':'
        """
        parts = model.split(":", 1)
        if len(parts) != 2:
            return model
        dt = parts[0]
        suf = parts[1]
        return {"datatype": dt, "suffix": suf}

    @staticmethod
    def _clean_keys(dictionary: dict) -> dict:
        """
        Copy dictionary entries if corresponding values
        are not empty (None, "", [], or {}).

        Parameters:
        -----------
        dictionary: dict
            Dictionary to cleanup

        Return:
        -------
        dict
            Cleaned up dictionary
        """
        res = {}
        for key, val in dictionary.items():
            if val is None:
                continue
            if isinstance(val, str) and val == "":
                continue
            if isinstance(val, (list, dict)) and not val:
                continue
            res[key] = val
        return res
