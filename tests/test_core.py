import json
import tempfile
import unittest
from pathlib import Path

from contextfossil.core import diff, load, snapshot


class ContextFossilTests(unittest.TestCase):
    def test_snapshot_redacts_environment_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "AGENTS.md").write_text("secret instruction", encoding="utf-8")
            snap = snapshot(root)
            self.assertEqual(list(snap["instruction_files"]), ["AGENTS.md"])
            self.assertNotIn("secret instruction", json.dumps(snap))
            self.assertIn("PATH", snap["environment_names"])

    def test_instruction_hash_changes_without_recording_contents(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "CLAUDE.md"
            path.write_text("one", encoding="utf-8")
            before = snapshot(root)
            path.write_text("two", encoding="utf-8")
            after = snapshot(root)
            result = diff(before, after)
            self.assertTrue(result["changed"])
            self.assertEqual(result["changes"][0]["kind"], "instruction_files.CLAUDE.md")
            self.assertNotIn("two", json.dumps(result))

    def test_diff_reports_environment_name_changes(self):
        before = {"schema": 1, "contextfossil": "0.1.0", "environment_names": ["A"], "git": {}, "platform": {}, "python": "3.12", "instruction_files": {}, "tools": {}}
        after = {**before, "environment_names": ["A", "B"]}
        result = diff(before, after)
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["changes"][0]["added"], ["B"])

    def test_load_rejects_unknown_schema(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.json"
            path.write_text('{"schema": 99}', encoding="utf-8")
            with self.assertRaises(ValueError):
                load(path)


if __name__ == "__main__":
    unittest.main()
