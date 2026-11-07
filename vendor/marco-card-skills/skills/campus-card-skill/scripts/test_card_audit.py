"""Regression tests for the read-only audit; no live cards or platform writes."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).with_name("card-audit.py")
SPEC = importlib.util.spec_from_file_location("card_audit", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def taberna():
    return {"braindance": {
        "embeddedWorldBookCategories": [{"id": "rules"}],
        "embeddedWorldBook": [{"content": "A repair consumes one part.", "enabled": True,
                               "probability": 100, "triggerExpression": "NOT (__常驻__)",
                               "categoryId": "rules", "triggerAreas": [3, 4],
                               "insertionPosition": 1, "insertionPositions": [1]}]}}


class AuditTests(unittest.TestCase):
    def test_unknown_extensions_survive_read_only_audit(self):
        doc = taberna()
        doc["future_extension"] = {"nested": [1, 2]}
        original = copy.deepcopy(doc)
        self.assertFalse(MODULE.audit(doc)["errors"])
        self.assertEqual(doc, original)

    def test_st_character_and_standalone_wrappers(self):
        for doc in ({"spec": "chara_card_v3", "data": {"name": "Mechanic", "description": ""}},
                    {"entries": {"0": {"uid": 0, "content": "shop", "key": ["shop"]}}}):
            self.assertFalse(MODULE.audit(doc)["errors"])

    def test_dangling_category_fails_even_when_json_parses(self):
        doc = taberna()
        doc["braindance"]["embeddedWorldBook"][0]["categoryId"] = "missing"
        self.assertTrue(MODULE.audit(doc)["errors"])

    def test_duplicate_category_and_entry_ids(self):
        doc = taberna()
        doc["braindance"]["embeddedWorldBookCategories"].append({"id": "rules"})
        self.assertTrue(MODULE.audit(doc)["errors"])
        self.assertTrue(MODULE.audit({"entries": [
            {"uid": 0, "content": "a"}, {"uid": 0, "content": "b"}]})["errors"])

    def test_disabled_content_does_not_count_as_enabled(self):
        doc = taberna()
        doc["braindance"]["embeddedWorldBook"][0]["enabled"] = False
        stats = MODULE.audit(doc)["stats"]
        self.assertEqual(stats["disabled_entries"], 1)
        self.assertEqual(stats["enabled_entry_chars"], 0)

    def test_arbitrary_not_is_not_classified_as_constant(self):
        doc = taberna()
        doc["braindance"]["embeddedWorldBook"][0]["triggerExpression"] = "NOT (夜晚)"
        stats = MODULE.audit(doc)["stats"]
        self.assertEqual(stats["constant_candidate_chars"], 0)
        self.assertGreater(stats["conditional_candidate_chars"], 0)

    def test_zero_probability_is_valid_but_boolean_is_not(self):
        doc = taberna()
        entry = doc["braindance"]["embeddedWorldBook"][0]
        entry["probability"] = 0
        self.assertFalse(MODULE.audit(doc)["errors"])
        entry["probability"] = True
        self.assertTrue(MODULE.audit(doc)["errors"])

    def test_bad_shapes_produce_diagnostics_not_tracebacks(self):
        for doc in ([], {"braindance": []}, {"entries": None},
                    {"entries": [None]}, {"entries": [{"content": [], "key": "shop"}]},
                    {"spec": "chara_card_v2", "data": {"character_book": []}}):
            with self.subTest(doc=doc):
                self.assertTrue(MODULE.audit(doc)["errors"])

    def test_style_is_candidate_only_and_script_is_excluded(self):
        doc = taberna()
        doc["braindance"]["firstMessage"] = '她数了数纽扣。<script>const s="一丝";</script>'
        result = MODULE.audit(doc, "bai-miao")
        self.assertFalse(result["errors"])
        self.assertEqual([x["term"] for x in result["style_candidates"]], ["纽扣"])

    def test_cli_exit_codes_and_no_rewrites(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "card.json"
            warning = taberna()
            warning["braindance"]["embeddedWorldBook"][0]["triggerExpression"] = ""
            for data, expected in (("{bad json", 2), ("[]", 1),
                                   (json.dumps(warning, ensure_ascii=False), 0)):
                path.write_text(data, encoding="utf-8")
                before = path.read_bytes()
                result = subprocess.run([sys.executable, str(SCRIPT), str(path)],
                                        capture_output=True, check=False)
                self.assertEqual(result.returncode, expected, result.stderr)
                json.loads(result.stdout.decode("utf-8"))
                self.assertEqual(path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
