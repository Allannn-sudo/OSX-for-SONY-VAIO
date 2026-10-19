"""Portable branch-preparation tests using temporary, synthetic snapshots only."""

import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


SPEC = importlib.util.spec_from_file_location(
    "prepare_model_branch", Path(__file__).resolve().parents[1] / "scripts" / "prepare_model_branch.py"
)
HELPER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HELPER)


class ModelBranchPreparationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / ".github/branch-readmes").mkdir(parents=True)
        for source, destination in HELPER.TEMPLATES:
            (self.root / source).write_text("# " + source + "\n中文 / English\n", encoding="utf-8")
            (self.root / destination).write_text("Original project overview\n", encoding="utf-8")
        (self.root / "github-ph.jpg").write_bytes(b"synthetic fixture only\x00\xff")
        (self.root / "evidence").mkdir()
        self.layout = {"repository": HELPER.REPOSITORY, "project_branch": "main",
                       "model_branches": {HELPER.MODEL: {"fixture": "keep"}},
                       "active_readme": "project"}
        (self.root / HELPER.LAYOUT).write_text(json.dumps(self.layout))
        (self.root / HELPER.MANIFEST).write_text("old manifest\n", encoding="utf-8")

    def prepare(self, repository=HELPER.REPOSITORY, model=HELPER.MODEL):
        HELPER.prepare_model_branch(self.root, repository, model)

    def assert_unchanged(self):
        self.assertEqual((self.root / "README.md").read_text(), "Original project overview\n")
        self.assertEqual((self.root / "README.en.md").read_text(), "Original project overview\n")
        self.assertEqual((self.root / HELPER.MANIFEST).read_text(), "old manifest\n")

    def test_both_readmes_copy_exact_template_bytes(self):
        self.prepare()
        for source, destination in HELPER.TEMPLATES:
            self.assertEqual((self.root / source).read_bytes(), (self.root / destination).read_bytes())

    def test_manifest_covers_final_contents_and_omits_itself(self):
        self.prepare()
        rows = (self.root / HELPER.MANIFEST).read_text().splitlines()
        names = []
        for row in rows:
            digest, name = row.split("  ", 1)
            self.assertEqual(digest, hashlib.sha256((self.root / name).read_bytes()).hexdigest())
            names.append(name)
        self.assertEqual(names, sorted(names))
        self.assertNotIn(HELPER.MANIFEST, names)
        self.assertIn("github-ph.jpg", names)
        self.assertIn(".github/branch-readmes/vgn-y18c.zh-CN.md", names)

    def test_wrong_repository_refused_before_writes(self):
        with self.assertRaises(ValueError):
            self.prepare(repository="someone-else/unrelated")
        self.assert_unchanged()

    def test_wrong_model_refused_before_writes(self):
        with self.assertRaises(ValueError):
            self.prepare(model="../../main")
        self.assert_unchanged()

    def test_layout_marker_is_updated_without_losing_model_metadata(self):
        self.prepare()
        layout = json.loads((self.root / HELPER.LAYOUT).read_text())
        self.assertEqual(layout["active_readme"], HELPER.MODEL)
        self.assertEqual(layout["model_branches"], self.layout["model_branches"])

    def test_wrong_layout_repository_refused_before_writes(self):
        self.layout["repository"] = "someone-else/unrelated"
        (self.root / HELPER.LAYOUT).write_text(json.dumps(self.layout))
        with self.assertRaises(ValueError):
            self.prepare()
        self.assert_unchanged()

    def test_malformed_layout_refused_before_writes(self):
        (self.root / HELPER.LAYOUT).write_text("not JSON")
        with self.assertRaises(ValueError):
            self.prepare()
        self.assert_unchanged()

    def test_missing_second_template_does_not_partially_replace_readmes(self):
        (self.root / HELPER.TEMPLATES[1][0]).unlink()
        with self.assertRaises(OSError):
            self.prepare()
        self.assert_unchanged()

    def test_empty_template_refused_before_writes(self):
        (self.root / HELPER.TEMPLATES[1][0]).write_bytes(b" \n")
        with self.assertRaises(ValueError):
            self.prepare()
        self.assert_unchanged()

    def test_invalid_utf8_template_refused_before_writes(self):
        (self.root / HELPER.TEMPLATES[1][0]).write_bytes(b"\xff")
        with self.assertRaises(UnicodeError):
            self.prepare()
        self.assert_unchanged()

    def test_template_symlink_refused(self):
        source = self.root / HELPER.TEMPLATES[0][0]
        source.unlink()
        source.symlink_to(self.root / "README.md")
        with self.assertRaises(ValueError):
            self.prepare()
        self.assert_unchanged()

    def test_manifest_symlink_refused_without_writing_target(self):
        outside = self.root / "unrelated.txt"
        outside.write_text("preserve me")
        (self.root / HELPER.MANIFEST).unlink()
        (self.root / HELPER.MANIFEST).symlink_to(outside)
        with self.assertRaises(ValueError):
            self.prepare()
        self.assertEqual(outside.read_text(), "preserve me")
        self.assertEqual((self.root / "README.md").read_text(), "Original project overview\n")

    def test_readme_symlink_refused_without_writing_target(self):
        outside = self.root / "unrelated.txt"
        outside.write_text("preserve me")
        (self.root / "README.md").unlink()
        (self.root / "README.md").symlink_to(outside)
        with self.assertRaises(ValueError):
            self.prepare()
        self.assertEqual(outside.read_text(), "preserve me")

    def test_git_and_python_runtime_metadata_are_excluded(self):
        (self.root / ".git").mkdir()
        (self.root / ".git/config").write_text("private fixture config")
        (self.root / "__pycache__").mkdir()
        (self.root / "__pycache__/module.pyc").write_bytes(b"cache")
        self.prepare()
        manifest = (self.root / HELPER.MANIFEST).read_text()
        self.assertNotIn(".git/config", manifest)
        self.assertNotIn("__pycache__", manifest)

    def test_ambiguous_filename_refused_before_writes(self):
        (self.root / "bad\nname.md").write_text("ambiguous")
        with self.assertRaises(ValueError):
            self.prepare()
        self.assert_unchanged()

    def test_repeated_preparation_is_idempotent(self):
        self.prepare()
        before = (self.root / HELPER.MANIFEST).read_bytes()
        self.prepare()
        self.assertEqual(before, (self.root / HELPER.MANIFEST).read_bytes())

    def test_manifest_refresh_preserves_project_readmes(self):
        HELPER.write_manifest(self.root)
        self.assertEqual((self.root / "README.md").read_text(), "Original project overview\n")
        self.assertEqual((self.root / HELPER.MANIFEST).read_bytes(), HELPER.manifest_bytes(self.root))


if __name__ == "__main__":
    unittest.main()
