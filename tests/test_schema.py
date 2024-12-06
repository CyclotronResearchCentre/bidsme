import unittest
import os
import glob
import logging

from bidsschematools import schema as bst
from bidsschematools import expressions

from bidsme.schema.BIDSschema import modalities
from bidsme.schema import parcing
from bidsme.schema import functs
from bidsme.schema import validate
from bidsme.schema import BIDSschema
from bidsme.schema import get_modality


class TestParcingSelectors(unittest.TestCase):

    def test_resolve_string(self):
        self.assertEqual(parcing.resolve("'test'", {}), "test")
        self.assertEqual(parcing.resolve("key", {"key": 3}), 3)

        with self.assertRaises(KeyError):
            parcing.resolve("test", {"key": 3})

    def test_resolve_bin(self):
        selector = "3 == 3"
        res = expressions.parse(selector)
        self.assertTrue(parcing.resolve(res, {}))

        selector = "3 in [1, 2, 'abc', 3]"
        res = expressions.parse(selector)
        self.assertTrue(parcing.resolve(res, {}))

        # testing in for non-iterable objects
        selector = "3 in 4"
        res = expressions.parse(selector)
        self.assertFalse(parcing.resolve(res, {}))

    def test_resolve_right(self):
        selector = "!false"
        res = expressions.parse(selector)
        self.assertTrue(parcing.resolve(res, {"false": False}))

    def test_resolve_function(self):
        selector = "intersects([1, 2, 3], [3, 4, 5])"
        res = expressions.parse(selector)
        self.assertEqual(parcing.resolve(res, {}), [3])

        selector = "match('abcde', '^ab[cde]{3}$')"
        res = expressions.parse(selector)
        self.assertEqual(parcing.resolve(res, {}), True)

        selector = 'intersects(sidecar.ReconFilterType, ["none"])'
        res = expressions.parse(selector)
        self.assertFalse(parcing.resolve(res, {"sidecar": {}}))

        with self.assertRaises(KeyError):
            selector = "fail('abcde', '^ab[cde]{3}$')"
            res = expressions.parse(selector)
            parcing.resolve(res, {})

    def test_resolve_array(self):
        selector = "[1, 2, 3]"
        res = expressions.parse(selector)
        self.assertEqual(parcing.resolve(res, {}), [1, 2, 3])

    def test_resolve_element(self):
        selector = "test[2]"
        res = expressions.parse(selector)
        self.assertEqual(parcing.resolve(res, {"test": [1, 2, 3]}), 3)

        selector = "[1, 2, 3][test]"
        res = expressions.parse(selector)
        self.assertEqual(parcing.resolve(res, {"test": 2}), 3)

    def test_resolve_proprety(self):
        selector = "test.abc"
        res = expressions.parse(selector)
        self.assertEqual(parcing.resolve(res, {"test": {"abc": 3}}), 3)

        with self.assertRaises(TypeError):
            selector = "'test'.abc"
            res = expressions.parse(selector)
            parcing.resolve(res, {"test": {"abc": 3}})

    def test_selector(self):
        res = parcing.test_selector("1 == 1", {})
        self.assertTrue(res)

        res = parcing.test_selector("1 == true", {})
        self.assertTrue(res)

    def test_unimplemented(self):
        with self.assertRaises(NotImplementedError):
            selector = expressions.Object("abc")
            parcing.resolve(selector, {})

        with self.assertRaises(TypeError):
            selector = expressions.ASTNode()
            parcing.resolve(selector, {})

    def test_real_examples(self):
        inputs = {"dataset": {"modalities": ["mri", "pet"]},
                  "datatype": "func",
                  "modality": "mri",
                  "suffix": "bold",
                  "extension": ".nii.gz",
                  "sidecar": {"RepetitionTime": 123},
                  }
        selections = ['datatype == "func"',
                      'suffix == "bold"',
                      '!("VolumeTiming" in sidecar)',
                      r'match(extension, "^\.nii(\.gz)?$")']
        for sel in selections:
            self.assertTrue(parcing.test_selector(sel, inputs))

    def test_all_selectors(self):
        inputs = {"dataset": {"modalities": ["mri", "pet"],
                              "datatypes": ["anat", "pet"]},
                  "datatype": "func",
                  "modality": "mri",
                  "suffix": "bold",
                  "extension": ".nii.gz",
                  "sidecar": {"RepetitionTime": 123,
                              "ReconMethodParameterLabels": "abc"
                              },
                  "json": {"RepetitionTime": 123},
                  "entity": {"task": "test"},
                  "entities": {}
                  }

        schema = bst.load_schema()
        rules = schema.rules.sidecars
        for dt in rules:
            for name, rule in rules[dt].items():
                if "selectors" not in rule:
                    continue
                for sel in rule["selectors"]:
                    try:
                        parcing.test_selector(sel, inputs)
                    except Exception as err:
                        raise Exception("{} {}: {}".format(dt, name, err))


class TestValidate(unittest.TestCase):

    def test_basic_types(self):
        # bool
        self.assertTrue(functs.test_boolean(None, True))
        self.assertFalse(functs.test_boolean(None, 1))

        # int
        item = {"type": "integer"}
        self.assertTrue(functs.test_integer(item, 3))
        self.assertFalse(functs.test_integer(item, 3.14))
        self.assertFalse(functs.test_integer(item, 'a'))

        # number
        self.assertTrue(functs.test_number(item, 3.14))
        self.assertFalse(functs.test_number(item, 'a'))

        # string
        self.assertTrue(functs.test_string(None, "abc"))
        self.assertFalse(functs.test_string(None, 1))

    def test_conditions(self):
        # limits
        item = {"minimum": 2}
        self.assertTrue(functs.test_limit(item, 2))
        self.assertFalse(functs.test_limit(item, 1))

        item = {"maximum": 2}
        self.assertTrue(functs.test_limit(item, 0))
        self.assertFalse(functs.test_limit(item, 3))

        item = {"exclusiveMinimum": 2}
        self.assertTrue(functs.test_limit(item, 3))
        self.assertFalse(functs.test_limit(item, 2))

        item = {"exclusiveMaximum": 2}
        self.assertTrue(functs.test_limit(item, 1))
        self.assertFalse(functs.test_limit(item, 2))

    def test_format(self):
        fmt = {"display_name": "Boolean"}
        self.assertEqual(functs.test_format("abc", fmt), "")

        fmt["pattern"] = "(true|false)"
        self.assertEqual(functs.test_format("true", fmt), "")

        self.assertEqual(functs.test_format("2", fmt),
                         "'2' do not match format Boolean "
                         "((true|false))")

    def test_array(self):
        item = {}
        self.assertEqual(validate.test_array(item, [1, 2, 3], {}), "")
        self.assertEqual(validate.test_array(item, "abc", {}),
                         "Not a list")

        item["minItems"] = 2
        self.assertEqual(validate.test_array(item, [1, 2], {}), "")
        self.assertEqual(validate.test_array(item, [1], {}),
                         "Number of elements below 2")

        item["maxItems"] = 3
        self.assertEqual(validate.test_array(item, [1, 2], {}), "")
        self.assertEqual(validate.test_array(item, [1, 2, 3, 4], {}),
                         "Number of elements above 3")

        item["items"] = {"type": "integer"}
        self.assertEqual(validate.test_array(item, [1, 2], {}), "")
        msg = validate.test_array(item, [1, "a"], {})
        self.assertTrue(msg.startswith("Failed for element 1:"))

    def test_object(self):
        item = {}
        self.assertEqual(validate.test_object(item, {"a": 1}, {}), "")
        self.assertEqual(validate.test_object(item, [1, 2], {}),
                         "Not an object")

        item["additionalProperties"] = {"type": "integer"}
        self.assertEqual(validate.test_object(item, {"a": 1}, {}), "")
        msg = validate.test_object(item, {"a": "b"}, {})
        self.assertTrue(msg.startswith("Failed for element a:"))

    def test_validate_value(self):
        schema = bst.load_schema()
        formats = schema.objects.formats

        item = {"type": "fail"}
        with self.assertRaises(KeyError):
            validate.validate_value(item, "abc", formats)

        item["type"] = "integer"
        self.assertEqual(validate.validate_value(item, 3, formats), "")
        self.assertEqual(validate.validate_value(item, "a", formats),
                         "'a' not of type integer")

        item["type"] = "string"
        with self.assertRaises(KeyError):
            item["format"] = "fail"
            validate.validate_value(item, '3', formats)

        item["format"] = "index"
        self.assertEqual(validate.validate_value(item, '3', formats), "")
        self.assertNotEqual(validate.validate_value(item, '-3', formats), "")

        item["enum"] = ["1", "2", "3"]
        self.assertEqual(validate.validate_value(item, '3', formats), "")
        self.assertEqual(validate.validate_value(item, '4', formats),
                         "'4' not in ['1', '2', '3']")

        item_m = {"anyOf": [item]}
        item_m["anyOf"].append({"type": "integer"})
        self.assertEqual(validate.validate_value(item_m, '3', formats), "")
        self.assertEqual(validate.validate_value(item_m, 3, formats), "")

        msg = validate.validate_value(item_m, 3.14, formats)
        self.assertTrue(msg.startswith("'3.14' failed for all in "))

    def test_real_types(self):
        schema = bst.load_schema()
        formats = schema.objects.formats

        item = {"type": "array", "items": {"type": "string"}}
        msg = validate.validate_value(item, ["a", "b", "c"], formats)
        self.assertEqual(msg, "")

        item = {'type': 'object',
                'additionalProperties': {'type': 'array',
                                         'items': {'type': 'number'},
                                         'minItems': 3, 'maxItems': 3}
                }
        test = {"NAS": [12.7, 21.3, 13.9],
                "LPA": [5.2, 11.3, 9.6],
                "RPA": [20.2, 11.3, 9.1]}
        msg = validate.validate_value(item, test, formats)
        self.assertEqual(msg, "")


class TestBIDSschema(unittest.TestCase):
    schemas = {}
    test_data = ""
    dfolders = []

    @classmethod
    def setUpClass(cls):
        # Loading all schemas
        cls.schemas = {key: BIDSschema(key)
                       for key, val in modalities.items()}

    def test_get_modality(self):
        self.assertEqual(get_modality("anat"), "mri")
        self.assertEqual(get_modality("eeg"), "eeg")
        self.assertIsNone(get_modality("test"))

    def test_split_name(self):
        # Correct file
        fname = "sub-012_ses-345_suf.nii.gz"
        ents, suf, ext = BIDSschema.split_fname(fname)
        self.assertEqual(ents, {"sub": "012", "ses": "345"})
        self.assertEqual(suf, "suf")
        self.assertEqual(ext, ".nii.gz")

        # No extension
        fname = "sub-012_ses-345_suf"
        with self.assertRaises(ValueError):
            BIDSschema.split_fname(fname)

        # Empty entity
        fname = "sub-012_ses-_suf.nii"
        with self.assertRaises(ValueError):
            BIDSschema.split_fname(fname)

    def test_get_models(self):
        self.assertEqual(BIDSschema._get_models("aaa:bbb"),
                         {"datatype": "aaa",
                          "suffix": "bbb"})
        self.assertEqual(BIDSschema._get_models("aaabbb"), "aaabbb")

    def test_clean_keys(self):
        in_dict = {"a": "abc", "b": None, "c": "", "d": {}}
        out_dict = {"a": "abc"}
        self.assertEqual(BIDSschema._clean_keys(in_dict), out_dict)

    def test_get_requirement_from_level(self):
        level = "required, addendum"
        lev, add = BIDSschema._get_requirement_from_level(level)
        self.assertEqual(lev, 0)
        self.assertEqual(add, "addendum")

        level = {"level": "required",
                 "level_addendum": "addendum"}
        lev, add = BIDSschema._get_requirement_from_level(level)
        self.assertEqual(lev, 0)
        self.assertEqual(add, "addendum")

        level = {"level": "required"}
        lev, add = BIDSschema._get_requirement_from_level(level)
        self.assertEqual(lev, 0)
        self.assertEqual(add, "")

        lev, add = BIDSschema._get_requirement_from_level("REQUIRED")
        self.assertEqual(lev, 0)

        lev, add = BIDSschema._get_requirement_from_level("RECOMMENDED")
        self.assertEqual(lev, 1)

        lev, add = BIDSschema._get_requirement_from_level("OPTIONAL")
        self.assertEqual(lev, 2)

        lev, add = BIDSschema._get_requirement_from_level("DEPRECATED")
        self.assertEqual(lev, 3)

        with self.assertRaises(KeyError):
            BIDSschema._get_requirement_from_level("None")

    def test_entity_rule(self):
        with self.assertLogs(level=logging.INFO) as cm:
            rule = BIDSschema.get_ent_rule("meg", "meg")
        self.assertEqual(cm.output, ["INFO:bidsme.schema.BIDSschema:"
                                     "Matched meg/meg rule"])
        entities = list(rule.entities.keys())
        self.assertEqual(entities,
                         ["subject", "session", "task",
                          "acquisition", "run", "processing",
                          "split"])

        with self.assertLogs(level=logging.INFO) as cm:
            rule = BIDSschema.get_ent_rule("calibration")
        self.assertEqual(cm.output, ["INFO:bidsme.schema.BIDSschema:"
                                     "Matched meg/calibration rule"])
        entities = list(rule.entities.keys())
        self.assertEqual(entities,
                         ["subject", "session", "acquisition"])

        rule = BIDSschema.get_ent_rule("rule_dont_exists")
        self.assertIsNone(rule)

    def test_get_sidecar_rule(self):
        # Testing on restricted ruleset
        ruleset = {"perf": BIDSschema._schema.rules.sidecars.asl}
        inputs = {"datatype": "perf",
                  "suffix": "asl",
                  "sidecar": {"M0Type": "Estimate"}}
        rules = BIDSschema.get_sidecar_rule(ruleset=ruleset, **inputs)
        rules_list = list(rules.keys())
        self.assertCountEqual(
                      ["perf/MRIASLTextOnly",
                       "perf/MRIASLCommonMetadataFields",
                       "perf/MRIASLCommonMetadataFieldsM0TypeReq"
                       ],
                      rules_list)

        # Testing with skip
        inputs = {"datatype": "perf",
                  "suffix": "asl",
                  }
        rules = BIDSschema.get_sidecar_rule(
                skip="(sidecar)",
                ruleset=ruleset, **inputs)
        rules_list = list(rules.keys())
        self.assertCountEqual(
                  ['perf/MRIASLTextOnly',
                   'perf/MRIASLCommonMetadataFields',
                   'perf/MRIASLCommonMetadataFieldsM0TypeRec',
                   'perf/MRIASLCommonMetadataFieldsM0TypeReq',
                   'perf/MRIASLCommonMetadataFieldsBackgroundSuppressionOpt',
                   'perf/MRIASLCommonMetadataFieldsBackgroundSuppressionReq',
                   'perf/MRIASLCommonMetadataFieldsVascularCrushingOpt',
                   'perf/MRIASLCommonMetadataFieldsVascularCrushingRec',
                   'perf/MRIASLCaslPcaslSpecific',
                   'perf/MRIASLPcaslSpecific',
                   'perf/MRIASLCaslSpecific',
                   'perf/MRIASLPaslSpecific',
                   'perf/MRIASLPASLSpecificBolusCutOffFlagFalse',
                   'perf/MRIASLPaslSpecificBolusCutOffFlagTrue'
                   ],
                  rules_list)

    def test_validate_name(self):
        rule = BIDSschema.get_ent_rule("anat", "T1w")

        # Correct name
        entities = {"sub": "abc",
                    "ses": "def",
                    "rec": "ghi",
                    "run": "01",
                    "part": "phase"}
        self.assertTrue(BIDSschema.validate_name(entities, rule))

        # Missing required entity
        entities = {"ses": "def",
                    "rec": "ghi",
                    "run": "01",
                    "part": "phase"}
        with self.assertLogs(level=logging.ERROR) as cm:
            self.assertFalse(BIDSschema.validate_name(entities, rule))
        self.assertEqual(cm.output, ["ERROR:bidsme.schema.BIDSschema:"
                                     "Missing required entity Subject (sub)"])

        # Invalid entity
        entities = {"sub": "abc",
                    "ses": "def",
                    "rec": "ghi",
                    "run": "test",
                    "part": "phase"}
        with self.assertLogs(level=logging.ERROR) as cm:
            self.assertFalse(BIDSschema.validate_name(entities, rule))
        msg = cm.output[0]
        self.assertTrue(msg.startswith("ERROR:bidsme.schema.BIDSschema:"
                                       "Invalid entity 'run-test'"))

        # Entities out of order
        entities = {"sub": "abc",
                    "ses": "def",
                    "run": "01",
                    "rec": "ghi",
                    "part": "phase"}
        with self.assertLogs(level=logging.ERROR) as cm:
            self.assertFalse(BIDSschema.validate_name(entities, rule))
        msg = cm.output[0]
        self.assertTrue(msg.startswith("ERROR:bidsme.schema.BIDSschema:"
                                       "Entities do not follow "
                                       "expected order"))

        # Extra entities
        entities = {"sub": "abc",
                    "ses": "def",
                    "rec": "ghi",
                    "run": "01",
                    "part": "phase",
                    "test": "test"}
        with self.assertLogs(level=logging.ERROR) as cm:
            self.assertFalse(BIDSschema.validate_name(entities, rule))
        msg = cm.output[0]
        self.assertEqual(msg, "ERROR:bidsme.schema.BIDSschema:"
                         "Found following extra entities: "
                         "['test']")

    def test_validate_sidecar(self):
        # Valid sidecar
        ruleset = {"perf": BIDSschema._schema.rules.sidecars.asl}
        inputs = {"datatype": "perf",
                  "suffix": "asl",
                  "sidecar": {"M0Type": "Estimate"}}
        rules = BIDSschema.get_sidecar_rule(ruleset=ruleset, **inputs)

        sidecar = {"ArterialSpinLabelingType": "CASL",
                   "PostLabelingDelay": 0.1,
                   "RepetitionTimePreparation": 0.1,
                   "BackgroundSuppression": False,
                   "M0Type": "Absent",
                   "TotalAcquiredPairs": 1,
                   "M0Estimate": 3
                   }
        self.assertTrue(BIDSschema.validate_sidecar(sidecar, rules))

        # Missing required
        sidecar = {"ArterialSpinLabelingType": "CASL",
                   "RepetitionTimePreparation": 0.1,
                   "BackgroundSuppression": False,
                   "M0Type": "Absent",
                   "TotalAcquiredPairs": 1,
                   "M0Estimate": 3
                   }
        with self.assertLogs(level=logging.ERROR) as cm:
            self.assertFalse(BIDSschema.validate_sidecar(sidecar, rules))
        msg = cm.output[0]
        self.assertTrue(msg.startswith("ERROR:bidsme.schema.BIDSschema:"
                                       "Missing required field "
                                       "Post Labeling Delay"))

        # Invalid field value
        sidecar = {"ArterialSpinLabelingType": "CASL",
                   "PostLabelingDelay": -1,
                   "RepetitionTimePreparation": 0.1,
                   "BackgroundSuppression": False,
                   "M0Type": "Absent",
                   "TotalAcquiredPairs": 1,
                   "M0Estimate": 3
                   }
        with self.assertLogs(level=logging.ERROR) as cm:
            self.assertFalse(BIDSschema.validate_sidecar(sidecar, rules))
        msg = cm.output[0]
        self.assertEqual(msg, "ERROR:bidsme.schema.BIDSschema:"
                         "Rule perf/MRIASLCommonMetadataFields failed")
        msg = cm.output[1]
        self.assertTrue(msg.startswith("ERROR:bidsme.schema.BIDSschema:"
                                       "Invalid field value "
                                       "'PostLabelingDelay:-1'"))

        # Invalid extra fields
        sidecar = {"ArterialSpinLabelingType": "CASL",
                   "PostLabelingDelay": 0.1,
                   "RepetitionTimePreparation": 0.1,
                   "BackgroundSuppression": False,
                   "M0Type": "Absent",
                   "TotalAcquiredPairs": 1,
                   "M0Estimate": 3,
                   "EMGChannelCount": -1
                   }
        with self.assertLogs(level=logging.ERROR) as cm:
            self.assertTrue(BIDSschema.validate_sidecar(sidecar, rules))
        msg = cm.output[0]
        self.assertTrue(msg.startswith("ERROR:bidsme.schema.BIDSschema:"
                                       "Extra field 'EMGChannelCount' "
                                       "do not match any rules"))
        msg = cm.output[1]
        self.assertTrue(msg.startswith("ERROR:bidsme.schema.BIDSschema:"
                                       "Invalid field value "
                                       "'EMGChannelCount:-1' -- '-1' not"
                                       " of type integer"))

        # Testing deprecated
        rules = {"pet/PETTime": BIDSschema._schema.rules.sidecars.pet.PETTime}
        sidecar = {"TimeZero": "00:00:00",
                   "ScanStart": 0,
                   "InjectionStart": 0,
                   "FrameTimesStart": [],
                   "FrameDuration": [],
                   "ScanDate": "2020-12-12"
                   }
        with self.assertLogs(level=logging.WARNING) as cm:
            self.assertTrue(BIDSschema.validate_sidecar(sidecar, rules))
        msg = cm.output[0]
        self.assertEqual(msg, "WARNING:bidsme.schema.BIDSschema:"
                         "Field 'ScanDate' is deprecated")

    def test_validation(self):
        # Valid name
        fname = "anat/sub-123_ses-456_T1w.nii"
        sidecar = {}
        self.assertTrue(BIDSschema.validate(fname, sidecar))

        # invalid name
        fname = "anat/sub-123_ses-456_T1w"
        with self.assertLogs(level=logging.ERROR):
            self.assertFalse(BIDSschema.validate(fname, sidecar))

        # No rule
        fname = "anat/sub-123_ses-456_TTT.nii"
        with self.assertLogs(level=logging.ERROR) as cm:
            self.assertFalse(BIDSschema.validate(fname, sidecar))
        self.assertEqual(cm.output, ["ERROR:bidsme.schema.BIDSschema:"
                                     "No file rule matching datatype "
                                     "'anat' and suffix 'TTT'"])

        # Wrong extension
        fname = "anat/sub-123_ses-456_T1w.dcm"
        with self.assertLogs(level=logging.WARNING):
            self.assertTrue(BIDSschema.validate(fname, sidecar))

    def test_get_entities(self):
        mri = BIDSschema("mri")
        model = "anat:T1w"
        res = mri.get_entities(model)
        self.assertEqual(res, {"task": None,
                               "acq": None,
                               "ce": None,
                               "rec": None,
                               "run": None,
                               "echo": None,
                               "part": None,
                               "chunk": None})
        model = "nonparametric"
        res = mri.get_entities(model)
        self.assertEqual(res, {"task": None,
                               "acq": None,
                               "ce": None,
                               "rec": None,
                               "run": None,
                               "echo": None,
                               "part": None,
                               "chunk": None})

        model = "<none>"
        self.assertEqual(mri.get_entities(model), {})

        model = "anat:TTT"
        with self.assertLogs(level=logging.ERROR):
            self.assertEqual(mri.get_entities(model), {})

    def test_get_sidecar(self):
        eeg = BIDSschema("eeg")
        res = eeg.get_sidecar(datatype="eeg", suffix="physio")
        sidecar = {'SamplingFrequency': '<<placeholder>>',
                   'StartTime': '<<placeholder>>',
                   'Columns': '<<placeholder>>',
                   'Manufacturer': '',
                   'ManufacturersModelName': '',
                   'SoftwareVersions': '',
                   'DeviceSerialNumber': ''
                   }
        self.assertEqual(res, sidecar)


if __name__ == '__main__':
    unittest.main()
