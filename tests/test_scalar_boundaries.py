"""Regression coverage for the supported YAML scalar and list subset."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "project-memory" / "scripts"
sys.path.insert(0, str(SCRIPTS))
import metadata_frontmatter as frontmatter


def parse(block):
    return frontmatter.parse_frontmatter(f"---\n{block}\n---\nBody\n")[0]


class ScalarBoundariesTests(unittest.TestCase):
    def test_mapping_colon_requires_value_separation(self):
        for line in ("title:Roadmap", 'title:"Roadmap"', "custom:#comment"):
            with self.subTest(line=line), self.assertRaises(ValueError):
                parse(line)

    def test_mapping_separation_retains_empty_fields_and_literal_colons(self):
        self.assertEqual(
            parse("empty:\nspaces:  \ntabs:\tvalue\nlink: https://example.test/a:b"),
            {"empty": None, "spaces": None, "tabs": "value", "link": "https://example.test/a:b"},
        )

    def test_cli_rejects_mapping_without_separation_and_preserves_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repair = [sys.executable, str(SCRIPTS / "repair_metadata.py"), "--root", str(root)]
            self.assertEqual(subprocess.run(repair, capture_output=True).returncode, 0)
            path = root / "docs" / "TASKS.md"
            original = path.read_text(encoding="utf-8").replace("title: Current Tasks", "title:Roadmap")
            path.write_text(original, encoding="utf-8")
            validate = [sys.executable, str(SCRIPTS / "validate_metadata.py"), "--root", str(root)]
            self.assertEqual(subprocess.run(validate, capture_output=True).returncode, 1)
            self.assertEqual(subprocess.run(repair + ["--touch"], capture_output=True).returncode, 1)
            self.assertEqual(path.read_text(encoding="utf-8"), original)

    def test_inline_comments_and_literal_hashes(self):
        block = r'''plain: It's a "fine" day # comment
hash: issue#123
single: 'It''s # literal' # comment
double: "A \"quote\" # literal" # comment
items:
  - plain's "quote" # comment
  - issue#123
  - 'It''s # literal' # comment
  - "A \"quote\" # literal" # comment'''
        self.assertEqual(parse(block), {
            "plain": '''It's a "fine" day''', "hash": "issue#123",
            "single": "It's # literal", "double": 'A "quote" # literal',
            "items": ['plain\'s "quote"', "issue#123", "It's # literal", 'A "quote" # literal'],
        })

    def test_comment_only_value_can_start_a_block_list(self):
        self.assertEqual(parse("tags: # comment\n  - one # comment\n  - two"),
                         {"tags": ["one", "two"]})

    def test_unsupported_yaml_objects_are_rejected_in_scalar_and_list(self):
        values = ("{key: value}", "[one, two]", "key: value", "&anchor value",
                  "*anchor", "!tag value", "|", ">", "]", "}", ",word")
        for value in values:
            for block in (f"custom: {value}", f"custom:\n  - {value}"):
                with self.subTest(block=block), self.assertRaises(ValueError):
                    parse(block)

    def test_quoted_yaml_constructs_remain_literal_strings(self):
        values = ("{key: value}", "[one, two]", "key: value", "&anchor value",
                  "*anchor", "!tag value", "|", ">", "]", "}", ",word")
        for value in values:
            quoted = json.dumps(value)
            with self.subTest(value=value):
                self.assertEqual(parse(f"custom: {quoted}\nitems:\n  - {quoted}"),
                                 {"custom": value, "items": [value]})

    def test_ambiguous_strings_are_quoted_in_scalars_and_lists(self):
        values = ("true", "False", "null", "~", "123", "-1", "1.5", "1e3",
                  "0x10", "2026-11-09", "yes", "NO", "on", "OFF", "y", "N",
                  "+12", ".inf", ".NaN", ".5", "0123", "0o17", "0b11", "1:20",
                  "2026-11-09T12:00:00Z")
        for value in values:
            with self.subTest(value=value):
                data = {"custom": value, "items": [value]}
                rendered = frontmatter.render_frontmatter(data)
                lines = rendered.splitlines()
                self.assertIn(lines[0], (f'custom: "{value}"', f"custom: '{value}'"))
                self.assertIn(lines[2], (f'  - "{value}"', f"  - '{value}'"))
                self.assertEqual(parse(rendered.rstrip("\n")), data)

    def test_malformed_or_empty_list_scalars_are_rejected(self):
        values = ('"unterminated', "'unterminated", '"quoted" junk',
                  "'quoted'#adjacent", "# null item", "- nested", "? key", "key:\tvalue")
        for value in values:
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse(f"custom:\n  - {value}")

    def test_tab_separated_scalar_punctuation_is_quoted(self):
        for value in ("key:\tvalue", "literal\t# hash"):
            with self.subTest(value=value):
                data = {"custom": value, "items": [value]}
                rendered = frontmatter.render_frontmatter(data)
                self.assertIn(json.dumps(value), rendered)
                self.assertEqual(parse(rendered.rstrip("\n")), data)

    def test_unicode_spaces_are_scalar_content(self):
        value = "\u00a0literal\u00a0# hash\u00a0"
        data = {"custom": value, "items": [value]}
        self.assertEqual(parse(f"custom: {value}\nitems:\n  - {value}"), data)
        self.assertEqual(parse(frontmatter.render_frontmatter(data).rstrip("\n")), data)

    def test_cli_repair_preserves_values_body_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            command = [sys.executable, str(SCRIPTS / "repair_metadata.py"), "--root", str(root)]
            self.assertEqual(subprocess.run(command, capture_output=True).returncode, 0)
            path = root / "docs" / "TASKS.md"
            original = path.read_text(encoding="utf-8")
            original = original.replace("title: Current Tasks", "title: 'It''s # literal' # comment")
            original = original.replace("---\n\n", 'custom: "true" # comment\nextras: # comment\n  - "123" # comment\n  - value#hash # comment\n---\n\n', 1)
            path.write_text(original, encoding="utf-8")
            before_body = frontmatter.parse_frontmatter(original)[1]
            result = subprocess.run(command + ["--touch"], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout)
            after = path.read_text(encoding="utf-8")
            data, body, _ = frontmatter.parse_frontmatter(after)
            self.assertEqual(body, before_body)
            self.assertEqual(data["title"], "It's # literal")
            self.assertEqual(data["custom"], "true")
            self.assertEqual(data["extras"], ["123", "value#hash"])
            self.assertIn('custom: "true"', after)
            self.assertIn('  - "123"', after)
            self.assertEqual(subprocess.run(command + ["--touch"], capture_output=True).returncode, 0)
            self.assertEqual(path.read_text(encoding="utf-8"), after)

    def test_cli_skips_unsupported_objects_without_rewriting(self):
        values = ("{key: value}", "[one, two]", "key: value", "&anchor value", "*anchor", "!tag value", "|", ">", "]", "}", ",word")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            command = [sys.executable, str(SCRIPTS / "repair_metadata.py"), "--root", str(root)]
            self.assertEqual(subprocess.run(command, capture_output=True).returncode, 0)
            path = root / "docs" / "TASKS.md"
            template = path.read_text(encoding="utf-8")
            for value in values:
                for line in (f"custom: {value}", f"custom:\n  - {value}"):
                    with self.subTest(line=line):
                        original = template.replace("---\n\n", f"{line}\n---\n\n", 1)
                        path.write_text(original, encoding="utf-8")
                        result = subprocess.run(command + ["--touch"], capture_output=True, text=True)
                        self.assertEqual(result.returncode, 1, result.stdout)
                        self.assertEqual(path.read_text(encoding="utf-8"), original)


if __name__ == "__main__":
    unittest.main()
