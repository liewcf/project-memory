"""Unit tests for the shared metadata helper module."""

from __future__ import annotations

import importlib.util
import os
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
METADATA_PATH = ROOT / "project-memory" / "scripts" / "metadata.py"


def load_metadata_module():
    scripts_dir = str(ROOT / "project-memory" / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location("metadata", METADATA_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {METADATA_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ConstantsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.m = load_metadata_module()

    def test_memory_files_tuple(self) -> None:
        self.assertEqual(
            self.m.MEMORY_FILES,
            (
                "PROJECT_CONTEXT.md",
                "DECISIONS.md",
                "TASKS.md",
                "CHANGELOG_WORK.md",
            ),
        )

    def test_docs_dir(self) -> None:
        self.assertEqual(self.m.DOCS_DIR, Path("docs"))

    def test_required_fields(self) -> None:
        self.assertIn("title", self.m.REQUIRED_FIELDS)
        self.assertIn("updated", self.m.REQUIRED_FIELDS)
        self.assertIn("related", self.m.REQUIRED_FIELDS)

    def test_allowed_doc_types(self) -> None:
        self.assertIn("context", self.m.ALLOWED_DOC_TYPES)
        self.assertIn("work_log", self.m.ALLOWED_DOC_TYPES)

    def test_allowed_statuses(self) -> None:
        self.assertIn("active", self.m.ALLOWED_STATUSES)
        self.assertIn("stable", self.m.ALLOWED_STATUSES)


class ResolveRootTests(unittest.TestCase):
    def setUp(self) -> None:
        self.m = load_metadata_module()

    def test_default_uses_cwd(self) -> None:
        self.assertEqual(self.m.resolve_root(), Path(os.getcwd()))

    def test_explicit_path(self) -> None:
        self.assertEqual(self.m.resolve_root("/tmp/foo"), Path("/tmp/foo"))


class ExpectedMetadataTests(unittest.TestCase):
    def setUp(self) -> None:
        self.m = load_metadata_module()
        self.today = date.today().isoformat()

    def test_project_context_status_is_stable(self) -> None:
        meta = self.m.expected_metadata("PROJECT_CONTEXT.md")
        self.assertEqual(meta["status"], "stable")
        self.assertEqual(meta["doc_type"], "context")

    def test_tasks_status_is_active(self) -> None:
        meta = self.m.expected_metadata("TASKS.md")
        self.assertEqual(meta["status"], "active")
        self.assertEqual(meta["doc_type"], "task_state")

    def test_all_files_have_dates(self) -> None:
        for fn in self.m.MEMORY_FILES:
            with self.subTest(filename=fn):
                meta = self.m.expected_metadata(fn)
                self.assertEqual(meta["created"], self.today)
                self.assertEqual(meta["updated"], self.today)

    def test_all_files_have_list_fields(self) -> None:
        for fn in self.m.MEMORY_FILES:
            with self.subTest(filename=fn):
                meta = self.m.expected_metadata(fn)
                self.assertIsInstance(meta["tags"], list)
                self.assertIsInstance(meta["audience"], list)
                self.assertIsInstance(meta["related"], list)


class DefaultBodyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.m = load_metadata_module()

    def test_all_files_have_minimal_body(self) -> None:
        for fn in self.m.MEMORY_FILES:
            with self.subTest(filename=fn):
                body = self.m.default_body(fn)
                self.assertTrue(body.startswith("#"))
                self.assertTrue(body.endswith("\n"))


class ParseFrontmatterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.m = load_metadata_module()

    def test_no_frontmatter(self) -> None:
        text = "# Hello\n\nSome content.\n"
        meta, body, had_fm = self.m.parse_frontmatter(text)
        self.assertEqual(meta, {})
        self.assertEqual(body, text)
        self.assertFalse(had_fm)

    def test_simple_frontmatter(self) -> None:
        text = "---\ntitle: Test\ndoc_type: context\n---\n# Body\n"
        meta, body, had_fm = self.m.parse_frontmatter(text)
        self.assertTrue(had_fm)
        self.assertEqual(meta["title"], "Test")
        self.assertEqual(meta["doc_type"], "context")
        self.assertEqual(body, "# Body\n")

    def test_quoted_string_double(self) -> None:
        text = '---\ntitle: "My Project"\n---\nBody\n'
        meta, body, had_fm = self.m.parse_frontmatter(text)
        self.assertTrue(had_fm)
        self.assertEqual(meta["title"], "My Project")

    def test_quoted_string_single(self) -> None:
        text = "---\ntitle: 'My Project'\n---\nBody\n"
        meta, body, had_fm = self.m.parse_frontmatter(text)
        self.assertTrue(had_fm)
        self.assertEqual(meta["title"], "My Project")

    def test_block_list(self) -> None:
        text = "---\ntags:\n  - project-memory\n  - context\n---\nBody\n"
        meta, body, had_fm = self.m.parse_frontmatter(text)
        self.assertTrue(had_fm)
        self.assertEqual(meta["tags"], ["project-memory", "context"])

    def test_rejects_flow_mapping(self) -> None:
        text = "---\nowner: { name: Liew }\n---\nBody\n"
        with self.assertRaisesRegex(ValueError, "Unsupported YAML"):
            self.m.parse_frontmatter(text)

    def test_rejects_nested_mapping(self) -> None:
        text = "---\ncomplex:\n  child: true\n---\nBody\n"
        with self.assertRaisesRegex(ValueError, "Unsupported nested"):
            self.m.parse_frontmatter(text)

    def test_empty_frontmatter(self) -> None:
        text = "---\n---\nBody\n"
        meta, body, had_fm = self.m.parse_frontmatter(text)
        self.assertTrue(had_fm)
        self.assertEqual(meta, {})

    def test_comments_ignored(self) -> None:
        text = "---\n# this is a comment\ntitle: Test\n---\nBody\n"
        meta, body, had_fm = self.m.parse_frontmatter(text)
        self.assertTrue(had_fm)
        self.assertEqual(meta["title"], "Test")


class RenderFrontmatterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.m = load_metadata_module()

    def test_renders_required_fields_in_order(self) -> None:
        meta = self.m.expected_metadata("TASKS.md")
        rendered = self.m.render_frontmatter(meta)
        lines = rendered.strip().split("\n")
        keys = [
            line.split(":")[0] for line in lines if ":" in line and not line.startswith("  ")
        ]
        self.assertEqual(
            keys,
            list(self.m.REQUIRED_FIELDS),
        )

    def test_unknown_fields_after_required(self) -> None:
        meta = self.m.expected_metadata("TASKS.md")
        meta["custom_field"] = "custom_value"
        rendered = self.m.render_frontmatter(meta)
        self.assertIn("custom_field: custom_value", rendered)
        lines = rendered.strip().split("\n")
        # custom_field should be last
        self.assertTrue(lines[-1].startswith("custom_field"))

    def test_list_rendering(self) -> None:
        meta = {"tags": ["a", "b"], "title": "T"}
        rendered = self.m.render_frontmatter(meta)
        self.assertIn("tags:\n  - a\n  - b", rendered)


class ValidateMetadataTests(unittest.TestCase):
    def setUp(self) -> None:
        self.m = load_metadata_module()

    def test_valid_metadata_passes(self) -> None:
        meta = self.m.expected_metadata("TASKS.md")
        errors = self.m.validate_metadata(meta, "TASKS.md")
        self.assertEqual(errors, [])

    def test_missing_required_field(self) -> None:
        meta = self.m.expected_metadata("TASKS.md")
        del meta["updated"]
        errors = self.m.validate_metadata(meta)
        self.assertTrue(any("Missing required field: updated" in e for e in errors))

    def test_invalid_doc_type(self) -> None:
        meta = self.m.expected_metadata("TASKS.md")
        meta["doc_type"] = "invalid_type"
        errors = self.m.validate_metadata(meta)
        self.assertTrue(any("Invalid doc_type" in e for e in errors))

    def test_invalid_status(self) -> None:
        meta = self.m.expected_metadata("TASKS.md")
        meta["status"] = "unknown"
        errors = self.m.validate_metadata(meta)
        self.assertTrue(any("Invalid status" in e for e in errors))

    def test_invalid_audience_value(self) -> None:
        meta = self.m.expected_metadata("TASKS.md")
        meta["audience"] = ["agent", "robot"]
        errors = self.m.validate_metadata(meta)
        self.assertTrue(any("Invalid audience value" in e for e in errors))

    def test_invalid_date_format(self) -> None:
        meta = self.m.expected_metadata("TASKS.md")
        meta["created"] = "June 13, 2026"
        errors = self.m.validate_metadata(meta)
        self.assertTrue(any("Invalid date format" in e for e in errors))

    def test_tags_must_be_list(self) -> None:
        meta = self.m.expected_metadata("TASKS.md")
        meta["tags"] = "not-a-list"
        errors = self.m.validate_metadata(meta)
        self.assertTrue(any("tags must be a list" in e for e in errors))

    def test_audience_must_be_list(self) -> None:
        meta = self.m.expected_metadata("TASKS.md")
        meta["audience"] = "agent"
        errors = self.m.validate_metadata(meta)
        self.assertTrue(any("audience must be a list" in e for e in errors))

    def test_related_must_be_list(self) -> None:
        meta = self.m.expected_metadata("TASKS.md")
        meta["related"] = "something"
        errors = self.m.validate_metadata(meta)
        self.assertTrue(any("related must be a list" in e for e in errors))


class RepairMetadataTests(unittest.TestCase):
    def setUp(self) -> None:
        self.m = load_metadata_module()
        self.today = date.today().isoformat()

    def test_fills_missing_fields(self) -> None:
        meta: dict[str, object] = {}
        repaired, changed = self.m.repair_metadata(meta, "TASKS.md")
        self.assertTrue(changed)
        self.assertEqual(repaired["title"], "Current Tasks")
        self.assertEqual(repaired["doc_type"], "task_state")
        self.assertEqual(repaired["created"], self.today)

    def test_preserves_valid_existing_values(self) -> None:
        meta = self.m.expected_metadata("TASKS.md")
        meta["title"] = "My Custom Title"
        meta["updated"] = "2026-01-01"
        repaired, changed = self.m.repair_metadata(meta, "TASKS.md")
        self.assertFalse(changed)
        self.assertEqual(repaired["title"], "My Custom Title")
        self.assertEqual(repaired["updated"], "2026-01-01")

    def test_repairs_invalid_doc_type(self) -> None:
        meta = self.m.expected_metadata("TASKS.md")
        meta["doc_type"] = "wrong"
        repaired, changed = self.m.repair_metadata(meta, "TASKS.md")
        self.assertTrue(changed)
        self.assertEqual(repaired["doc_type"], "task_state")

    def test_touch_bumps_updated(self) -> None:
        meta = self.m.expected_metadata("TASKS.md")
        meta["updated"] = "2026-01-01"
        repaired, changed = self.m.repair_metadata(
            meta, "TASKS.md", touch=True
        )
        self.assertEqual(repaired["updated"], self.today)

    def test_no_touch_preserves_updated(self) -> None:
        meta = self.m.expected_metadata("TASKS.md")
        meta["updated"] = "2026-01-01"
        repaired, changed = self.m.repair_metadata(meta, "TASKS.md")
        self.assertFalse(changed)
        self.assertEqual(repaired["updated"], "2026-01-01")

    def test_changing_other_field_bumps_updated(self) -> None:
        meta = self.m.expected_metadata("TASKS.md")
        meta["doc_type"] = "wrong"
        meta["updated"] = "2026-01-01"
        repaired, changed = self.m.repair_metadata(meta, "TASKS.md")
        self.assertTrue(changed)
        self.assertEqual(repaired["updated"], self.today)

    def test_repairs_non_list_tags(self) -> None:
        meta = self.m.expected_metadata("TASKS.md")
        meta["tags"] = "not-a-list"
        repaired, changed = self.m.repair_metadata(meta, "TASKS.md")
        self.assertTrue(changed)
        self.assertIsInstance(repaired["tags"], list)


class EnsureFrontmatterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.m = load_metadata_module()

    def test_adds_frontmatter_to_plain_markdown(self) -> None:
        text = "# Hello\n\nSome content.\n"
        result, status = self.m.ensure_frontmatter(text, "TASKS.md")
        self.assertEqual(status, "added")
        self.assertTrue(result.startswith("---\n"))
        self.assertIn("# Hello", result)

    def test_unchanged_when_valid(self) -> None:
        meta = self.m.expected_metadata("TASKS.md")
        fm = self.m.render_frontmatter(meta)
        text = f"---\n{fm}---\n\n# Body\n"
        result, status = self.m.ensure_frontmatter(text, "TASKS.md")
        self.assertEqual(status, "unchanged")

    def test_updates_invalid_frontmatter(self) -> None:
        text = "---\ntitle: Wrong\ndoc_type: bad_type\n---\n# Body\n"
        result, status = self.m.ensure_frontmatter(text, "TASKS.md")
        self.assertEqual(status, "updated")
        # doc_type should be repaired
        self.assertIn("doc_type: task_state", result)


if __name__ == "__main__":
    unittest.main()
