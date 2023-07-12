###############################################################################
# _bidsmap.py defined Bidsmap class which manages the interactions with
# recording identificating map
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


import os
import sys
import logging
from copy import deepcopy as copy
from collections import OrderedDict

from bidsme.tools import info
from bidsme.tools.yaml import yaml

from ._run import Run
from bidsme import Modules

logger = logging.getLogger(__name__)


class Bidsmap(object):
    __slots__ = ["Modules",
                 "filename",
                 "version"
                 ]

    def __init__(self, yamlfile='bidsmap.yaml'):
        """
        Parameters:
        -----------
        yamlfile: str
            YAML file to load
        """
        self.version = info.bidsversion()

        self.Modules = {mod: {t.__name__: dict() for t in types}
                        for mod, types in Modules.types_list.items()
                        }

        self.filename = os.path.basename(yamlfile)

        if not os.path.isfile(yamlfile):
            logger.info("{} not found. Bidsmap will be empty"
                        .format(yamlfile))
            return

        # Read the heuristics from the bidsmap file
        with open(yamlfile, 'r') as stream:
            try:
                yaml_map = yaml.load(stream)
                if yaml_map is None:
                    raise Exception("File don't contain any structure")
            except Exception:
                err = sys.exc_info()
                logger.error("Failed to load bidsmap from {}"
                             .format(yamlfile))
                logger.error("{}: {}".format(err[0], err[1]))
                raise

        if '__bids__' in yaml_map:
            ver = yaml_map['__bids__']
        else:
            ver = 'Unknown'

        if self.version != ver:
            logger.warning('BIDS version conflict: '
                           '{} was created using version {}, '
                           'but this is version {}'
                           .format(yamlfile, ver, info.version())
                           )

        # Over Modules (MRI, EEG etc..)
        for module in self.Modules:
            if module not in yaml_map or not yaml_map[module]:
                continue

            # Over Data formats (Nifty, Dicom etc...)
            for f_name, form in yaml_map[module].items():
                if not form:
                    continue
                if f_name not in self.Modules[module]:
                    logger.warning("Failed to find type {}/{} readed from {}. "
                                   .format(module, f_name, yamlfile))
                    continue
                # Over Modalities
                if not isinstance(form, dict):
                    logger.error("{}: {}/{} Malformed map, no modalities found"
                                 .format(os.path.basename(yamlfile),
                                         module, f_name))
                    raise TypeError("Malformed map")

                for m_name, modality in form.items():
                    if not Modules.selectByName(f_name, module)\
                            .isValidModality(m_name):
                        logger.warning("Modality {} not defined for {}/{}"
                                       .format(m_name, module, f_name))

                    self.Modules[module][f_name][m_name] =\
                        [None] * len(modality)
                    for ind, run in enumerate(modality):
                        if not run:
                            continue
                        try:
                            if m_name == Modules.ignoremodality:
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
                                        example=run.get("example"),
                                        json=run.get("json", OrderedDict())
                                        )
                            if "template" in run:
                                r.template = run["template"]
                            if "checked" in run:
                                r.checked = run["checked"]
                            if "model" in run:
                                r.model = run["model"]
                            if not r.checked:
                                r.provenance = None
                                r.example = None
                        except Exception as e:
                            logger.error("Malformed run in {}/{}/{}:{}"
                                         .format(module, f_name, m_name, ind)
                                         )
                            logger.error("{}:{}"
                                         .format(type(e).__name__, e.args))
                            raise
                        self.Modules[module][f_name][m_name][ind] = r

    def match_run(self, recording: object,
                  check_multiple: bool = True, fix: bool = False) -> tuple:
        """
        Matches run for given recording

        Parameters:
        -----------
        recording: Module.baseModule
            recording to match
        check_multiple: bool
            if True, proceeds over all runs and print warning if more
            than on run matches
        fix: bool
            if True, matched run attriburtes are fixed after the succesful
            match

        Returns
        -------
        tuple
            (modality, run index, run)
        """
        res_mod = None
        res_index = None
        res_run = None
        d = self.Modules[recording.Module()][recording.Type()]
        for modality, r_list in d.items():
            for idx, run in enumerate(r_list):
                if recording.match_run(run):
                    if check_multiple:
                        if res_mod is None:
                            recording.setLabels(run)
                            res_mod = modality
                            res_index = idx
                            res_run = run
                            if not run.provenance:
                                run.provenance = recording.currentFile()
                                run.checked = False
                                run.example = "{}/{}".format(
                                        modality,
                                        recording.getBidsname())
                            logger.debug("Checked run: {}/{}"
                                         .format(res_mod, res_index))
                        else:
                            logger.warning("{}/{}: also checks run: {}/{}"
                                           .format(res_mod, res_index,
                                                   modality, idx))
                    else:
                        recording.setLabels(run)
                        break
        if res_mod and res_mod != d[res_mod][res_index].modality:
            logger.warning("Run {}/{}/{} mismach modality {}"
                           .format(recording.formatIdentity(),
                                   res_mod,
                                   res_index,
                                   d[res_mod][res_index].modality))
        if fix and res_run:
            res_run = copy(res_run)
            for att, val in res_run.attribute.items():
                if val:
                    res_run.set_attribute(att, recording.getField(att))
            res_run.provenance = recording.currentFile()
        if res_run is None:
            res_run = Run(modality="__unknown__",
                          attribute=recording.attributes,
                          provenance=recording.currentFile())
        return (res_mod, res_index, res_run)

    def add_run(self, run: Run, module: str, form: str) -> tuple:
        """
        Add new run to list for given module and format.
        Added run is copied and behaves as independent
        object

        Parameters:
        -----------
        run: Run
            run to add
        module: str
            name of module to which run will be added
        form: str
            name of format to wich run will be added

        Returns:
        --------
        tuple
            (modality, run index, run)
        """
        run = copy(run)
        run.save()
        if run.modality in self.Modules[module][form]:
            self.Modules[module][form][run.modality].append(run)
        else:
            self.Modules[module][form][run.modality] = [run]
        return (run.modality,
                len(self.Modules[module][form][run.modality]) - 1,
                run)

    def save(self, filename: str,
             empty_modules: bool = False,
             empty_attributes: bool = True) -> None:
        """
        Writes map to YAML file

        Parameters:
        -----------
        filename: str
            name of file to be written
        empty_modules: bool
            if True, Modules with no runs will be saved
        empty_attributes: bool
            if True, Attributes with no values will be saved
        """
        logger.info("Writing bidsmap to: {}".format(filename))
        # TODO: use ruamel dump class ability
        # building dictionary
        d = dict()
        d["__bids__"] = self.version

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

    def checkSanity(self) -> tuple:
        """
        scans itself to check the sanity, in particular:
            if one file triggers several runs
            if several runs produce same example
            if run has no provenance
            if no suffix defined
        returns dictionary of counts of files and examples,
        and show warnings for no prevnance and empty suffix

        Returns:
        --------
        tuple
            (dict counters for files, dict counters for examples)
        """
        prov_duplicates = dict()
        example_duplicates = dict()

        for module in self.Modules:
            for f_name, form in self.Modules[module].items():
                for modality in form:
                    if modality == Modules.ignoremodality:
                        continue
                    for ind, r in enumerate(form[modality]):
                        if not r.suffix:
                            logger.warning("{}/{}/{}[{}]: Suffix not defined"
                                           .format(module, f_name,
                                                   modality, ind)
                                           )
                            continue
                        if not r.example:
                            logger.warning("{}/{}/{}[{}]: No matched "
                                           "recordings"
                                           .format(module, f_name,
                                                   modality, ind)
                                           )
                            continue
                        if r.provenance in prov_duplicates:
                            prov_duplicates[r.provenance] += 1
                        else:
                            prov_duplicates[r.provenance] = 1
                        if r.example in example_duplicates:
                            example_duplicates[r.example] += 1
                        else:
                            example_duplicates[r.example] = 1

        prov_duplicates = {key: val
                           for key, val in prov_duplicates.items()
                           if val > 1}
        example_duplicates = {key: val
                              for key, val in example_duplicates.items()
                              if val > 1}
        return (prov_duplicates, example_duplicates)

    def countRuns(self, module: str = "") -> tuple:
        """
        returns tuple (run, template, unchecked) of
        number of runs, template runs and unchecked
        runs respectively for given module (or all
        if empty string)

        Parameters:
        -----------
        module: str
            name of module to count

        Returns:
        --------
        tuple
            (total runs, template runs, unchecked runs)
        """
        unchecked = 0
        template = 0
        total = 0

        if module:
            if module not in self.Modules:
                return 0, 0, 0
            for f_name, form in self.Modules[module].items():
                for modality in form:
                    for r in form[modality]:
                        total += 1
                        if not r.checked:
                            unchecked += 1
                        if r.template:
                            template += 1
        else:
            for module in self.Modules:
                for f_name, form in self.Modules[module].items():
                    for modality in form:
                        for r in form[modality]:
                            total += 1
                            if not r.checked:
                                unchecked += 1
                            if r.template:
                                template += 1
        return total, template, unchecked
