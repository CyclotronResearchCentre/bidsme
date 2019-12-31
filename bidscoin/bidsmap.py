import os
import logging
from copy import deepcopy as copy
from tools.yaml import yaml
from collections import OrderedDict

from tools import info
from Modules.MRI import selector

logger = logging.getLogger(__name__)


def check_type(name, cls, val):
    if isinstance(val, cls):
        return val
    else:
        raise TypeError("{}: {} expected, {} recieved"
                        .format(name, str(cls), str(type(val))))


class Run(object):
    __slots__ = [
            "_modality",     # modality associeted with this run
            "attribute",     # dictionary of attr:regexp
            "entity",        # dictionary for run entities
            "json",          # dictionary for json fields
            "_suffix",       # suffix associated with run
            "_bk_modality",  # copy of self old values
            "_bk_attribute",
            "_bk_entity",
            "_bk_suffix",
            "_bk_json",
            "provenance",
            "writable",
            "template"
            ]

    def __init__(self, *,
                 modality: str = "",
                 attribute: OrderedDict = {},
                 entity: dict = {},
                 json:  OrderedDict = {},
                 suffix: str = "",
                 provenance: str = None
                 ):
        self.save()
        # self._bk_modality = None
        # self._bk_attribute = dict()
        # self._bk_entity = dict()
        # self._bk_suffix = None
        # self._bk_json = dicy()
        self.writable = True
        self.template = False

        self.provenance = provenance
        self._modality = check_type("modality", str, modality)
        self._suffix = check_type("suffix", str, suffix)
        self.attribute = dict(check_type("attribute", dict, attribute))
        self.entity = OrderedDict(check_type("entity", OrderedDict, entity))
        self.json = OrderedDict(check_type("json", OrderedDict, json))

    @property
    def modality(self):
        return self._modality

    @modality.setter
    def modality(self, value):
        if self._bk_modality is None:
            self._bk_modality = self._modality
        self.modality = value

    def restore_modality(self):
        if self._bk_modality is not None:
            self._modality = self._bk_modality
            self._bk_modality = None

    @property
    def suffix(self):
        return self._suffix

    @suffix.setter
    def suffix(self, value):
        if self._bk_suffix is None:
            self._bk_suffix = self._suffix
        self.suffix = value

    def restore_suffix(self):
        if self._bk_suffix is not None:
            self._suffix = self._bk_suffix
            self._bk_suffix = None

    def set_attribute(self, attr, val):
        # val = check_type("val", str, val)
        if isinstance(val, str):
            val = val.encode('unicode_escape').decode()
        attr = check_type("attr", str, attr)

        if attr in self.attribute:
            if self.attribute[attr] == val:
                return

            if attr not in self._bk_attribute:
                self._bk_attribute[attr] = self.attribute[attr]

            if val:
                self.attribute[attr] = val
            else:
                self.attribute.remove(attr)
            return

        else:
            if val == "":
                return
            self.attribute[attr] = val
            if attr not in self._bk_attribute:
                self._bk_attribute[attr] = None

    def set_entity(self, ent, val):
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

    def set_json_field(self, field, val):
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

    def restore_attribute(self, attr):
        self.__restore_val(attr,
                           self.attribute,
                           self._bk_attribute)

    def restore_attributes(self):
        for attr in self.attribute:
            self.__restore_val(attr,
                               self.attribute,
                               self._bk_attribute)

    def restore_entity(self, attr):
        self.__restore_val(attr,
                           self.entity,
                           self._bk_entity)

    def restore_entities(self):
        for attr in self.entity:
            self.__restore_val(attr,
                               self.entity,
                               self._bk_entity)

    def restore_json_field(self, attr):
        self.__restore_val(attr,
                           self.json,
                           self._bk_json)

    def restore_json(self):
        for attr in self.json:
            self.__restore_val(attr,
                               self.json,
                               self._bk_json)

    def restore(self):
        self.restore_modality()
        self.restore_suffix()
        self.restore_attributes()
        self.restore_entities()
        self.restore_json()

    def save(self):
        self._bk_modality = None
        self._bk_attribute = dict()
        self._bk_entity = dict()
        self._bk_jason = dict()
        self._bk_suffix = None

    def __restore_val(self, attr, dest, source):
        if attr not in source:
            return
        if source[attr] is None:
            if attr in dest:
                dest.remove(attr)
            return
        dest[attr] = source.pop(attr)

    def dump(self, empty_attributes=True):
        d = dict()
        d["provenance"] = self.provenance
        d["suffix"] = self.suffix
        d["template"] = self.template
        d["attributes"] = {k: v for k, v in self.attribute.items()
                           if empty_attributes or v
                           }
        d["bids"] = self.entity

        return d


class bidsmap(object):
    __slots__ = ["Modules",
                 "filename",
                 "version", "bidsignore",
                 "plugin_file", "plugin_options"]

    def __init__(self, yamlfile='bidsmap.yaml'):
        self.version = info.version()
        self.bidsignore = list()
        self.plugin_file = ""
        self.plugin_options = dict()

        self.Modules = {mod: {t.__name__: dict() for t in types}
                        for mod, types in selector.types_list.items()
                        }

        self.filename = os.path.basename(yamlfile)

        if not os.path.isfile(yamlfile):
            logger.info("{} not found. Bidsmap will be empty"
                        .format(yamlfile))
            return

        # Read the heuristics from the bidsmap file
        with open(yamlfile, 'r') as stream:
            yaml_map = yaml.load(stream)

        if 'version' in yaml_map['Options']:
            ver = yaml_map['Options']['version']
        else:
            ver = 'Unknown'

        if self.version != ver:
            logger.warning('BIDScoiner version conflict: '
                           '{} was created using version {}, '
                           'but this is version {}'
                           .format(yamlfile, ver, info.version())
                           )
        if 'PlugIns' in yaml_map:
            if 'path' in yaml_map['PlugIns']:
                self.plugin_file = yaml_map['PlugIns']['path']
            if 'options' in yaml_map['PlugIns'] \
                    and yaml_map['PlugIns']['options']:
                self.plugin_options = yaml_map['PlugIns']['options']

        if self.plugin_file:
            if not os.path.isfile(self.plugin_file):
                logger.error("Can't find plugin file {}"
                             .format(self.plugin_file))
                raise FileNotFoundError(self.plugin_file)

        # Over Modules (MRI, EEG etc..)
        for module in self.Modules:
            if module not in yaml_map or not yaml_map[module]:
                continue

            # Over Data formats (Nifty, Dicom etc...)
            for f_name, form in yaml_map[module].items():
                if not form:
                    continue
                if f_name not in self.Modules[module]:
                    logger.warning("Failed to find type {}/{} "
                                   "readed from {}"
                                   .format(module, f_name, yamlfile))
                    continue
                # Over Modalities
                for m_name, modality in form.items():
                    if not selector.select_by_name(f_name, module)\
                            .isValidModality(m_name):
                        logger.warning("Modality {} not defined for {}/{}"
                                       .format(m_name, module, f_name))
                        continue
                    self.Modules[module][f_name][m_name] =\
                        [None] * len(modality)
                    for ind, run in enumerate(modality):
                        if not run:
                            continue
                        json = OrderedDict()
                        if "json" in run:
                            json = run["json"]
                        try:
                            if m_name == selector.ignoremodality:
                                r = Run(modality=m_name,
                                        attribute=run["attributes"],
                                        entity=OrderedDict(),
                                        suffix="",
                                        provenance=run["provenance"])
                            else:
                                r = Run(modality=m_name,
                                        attribute=run["attributes"],
                                        entity=run["bids"],
                                        suffix=run["suffix"],
                                        provenance=run["provenance"],
                                        json=json
                                        )
                            if "template" in run:
                                r.template = run["template"]
                        except Exception as e:
                            logger.error("Malformed run in {}/{}/{}:{}"
                                         .format(module, f_name, m_name, ind)
                                         )
                            logger.error("{}:{}"
                                         .format(type(e).__name__, e.args))
                            continue
                        self.Modules[module][f_name][m_name][ind] = r

    def match_run(self, recording, check_multiple=True, fix=False):
        res_mod = None
        res_index = None
        res_run = None
        d = self.Modules[recording.Module][recording.get_type()]
        for modality, r_list in d.items():
            for idx, run in enumerate(r_list):
                if recording.match_run(run):
                    recording.set_labels(run)
                    recording.set_main_attributes(run)
                    if check_multiple:
                        if res_mod is None:
                            res_mod = modality
                            res_index = idx
                            res_run = run
                            if not run.provenance:
                                run.provenance = recording.currentFile()
                            logger.debug("Checked run: {}/{}"
                                         .format(res_mod, res_index))
                        else:
                            logger.warning("{}/{}: also checks run: {}/{}"
                                           .format(res_mod, res_index,
                                                   modality, idx))
                    else:
                        break
        if res_mod and res_mod != d[res_mod][res_index].modality:
            logger.warning("Run {}/{}/{}/{} mismach modality {}"
                           .format(recording.Module,
                                   recording.get_type(),
                                   res_mod,
                                   res_index,
                                   d[res_mod][res_index].modality))
        if fix and res_run:
            res_run = copy(res_run)
            for att, val in res_run.attribute.items():
                if val:
                    res_run.set_attribute(att, recording.get_field(att))
            res_run.provenance = recording.currentFile()
        return (res_mod, res_index, res_run)

    def add_run(self, run, module, form):
        run = copy(run)
        run.save()
        if run.modality in self.Modules[module][form]:
            self.Modules[module][form][run.modality].append(run)
        else:
            self.Modules[module][form][run.modality] = [run]
        return (run.modality,
                len(self.Modules[module][form][run.modality]) - 1,
                run)

    def save(self, filename, empty_modules=False, empty_attributes=True):
        logger.info("Writing bidsmap to: {}".format(filename))
        # TODO: use ruamel dump class ability
        # building dictionary
        d = dict()
        d['Options'] = {"version": self.version,
                        "bidsignore": self.bidsignore}
        d['PlugIns'] = {"path": None,
                        "options": None}
        # Modules
        for m_name, module in self.Modules.items():
            if not module and not empty_modules:
                continue
            d[m_name] = dict()
            # formats
            for f_name, form in module.items():
                if not form:
                    continue
                d[m_name][f_name] = dict()
                # modalities
                for mod_name, modality in form.items():
                    if not modality:
                        continue
                    d[m_name][f_name][mod_name] = [run.dump(empty_attributes)
                                                   for run in modality]
        with open(filename, 'w') as stream:
            yaml.dump(d, stream)
