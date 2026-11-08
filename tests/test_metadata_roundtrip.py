"""Regression tests for safe metadata scalar round trips."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "project-memory" / "scripts"
sys.path.insert(0, str(SCRIPTS))
import metadata_frontmatter
import metadata_repair


class ScalarRoundTripTests(unittest.TestCase):
    def test_scalar_and_list_values_round_trip(self):
        values = ["[Roadmap]", "{literal}", '"literal"', "'literal'", "C:\\temp\\path", " leading ", "", "a: b", "a:", "a # b", "quote ' and \"", "line\nbreak"]
        data = {"title": "[Roadmap]", "custom": values, "description": '"literal"'}
        rendered = metadata_frontmatter.render_frontmatter(data)
        parsed, _, _ = metadata_frontmatter.parse_frontmatter(f"---\n{rendered}---\n")
        self.assertEqual(parsed, data)

    def test_quoted_yaml_decoding(self):
        text = '''---\ntitle: "A \\\"quote\\\" and \\\\ path"\ncustom:\n  - 'It''s [fine]'\n  - "line\\nnext"\n---\n'''
        parsed, _, _ = metadata_frontmatter.parse_frontmatter(text)
        self.assertEqual(parsed["title"], 'A "quote" and \\ path')
        self.assertEqual(parsed["custom"], ["It's [fine]", "line\nnext"])

    def test_unicode_controls_and_separators_render_as_ascii_escapes(self):
        for escape in ("009f", "0085", "2028", "2029", "fffe", "ffff"):
            with self.subTest(escape=escape):
                parsed, _, _ = metadata_frontmatter.parse_frontmatter(
                    f'---\ntitle: "before\\u{escape}after"\n---\n'
                )
                rendered = metadata_frontmatter.render_frontmatter(parsed)
                self.assertIn(f"\\u{escape}", rendered)
                self.assertEqual(
                    metadata_frontmatter.parse_frontmatter(f"---\n{rendered}---\n")[0], parsed
                )
                list_data = {"tags": [parsed["title"]]}
                rendered_list = metadata_frontmatter.render_frontmatter(list_data)
                self.assertIn(f"\\u{escape}", rendered_list)
                self.assertEqual(
                    metadata_frontmatter.parse_frontmatter(f"---\n{rendered_list}---\n")[0], list_data
                )

    def test_surrogate_pairs_are_accepted_but_lone_surrogates_rejected(self):
        parsed, _, _ = metadata_frontmatter.parse_frontmatter(
            '---\ntitle: "\\ud83d\\ude00"\n---\n'
        )
        self.assertEqual(parsed["title"], "😀")
        for escape in ("d800", "dc00"):
            with self.subTest(escape=escape):
                with self.assertRaises(ValueError):
                    metadata_frontmatter.parse_frontmatter(
                        f'---\ntitle: "\\u{escape}"\n---\n'
                    )

    def test_quoted_supplementary_unicode_remains_literal(self):
        data = {"title": "[😀]", "tags": ["[😀]"]}
        rendered = metadata_frontmatter.render_frontmatter(data)
        self.assertEqual(rendered.count("😀"), 2)
        self.assertNotIn("\\ud83d", rendered.lower())
        self.assertNotIn("\\ude00", rendered.lower())
        self.assertEqual(
            metadata_frontmatter.parse_frontmatter(f"---\n{rendered}---\n")[0], data
        )

    def test_cli_does_not_publish_lone_surrogate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            command = [sys.executable, str(SCRIPTS / "repair_metadata.py"), "--root", str(root)]
            self.assertEqual(subprocess.run(command, capture_output=True).returncode, 0)
            path = root / "docs" / "TASKS.md"
            original = path.read_text().replace("title: Current Tasks", 'title: "\\ud800"')
            path.write_text(original)
            result = subprocess.run(command + ["--touch"], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(path.read_text(), original)

    def test_generated_metadata_must_match_before_return(self):
        for rendered in ("title: wrong\n", "title: [unsupported]\n"):
            with self.subTest(rendered=rendered):
                with patch.object(metadata_repair, "render_frontmatter", return_value=rendered):
                    with self.assertRaises(ValueError):
                        metadata_repair.ensure_frontmatter("# Body\n", "TASKS.md")

    def test_cli_touch_then_validate_and_repeat(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            def run(script, *args):
                return subprocess.run([sys.executable, str(SCRIPTS / script), "--root", str(root), *args], text=True, capture_output=True)
            self.assertEqual(run("repair_metadata.py").returncode, 0)
            path = root / "docs" / "TASKS.md"
            original = path.read_text().replace("title: Current Tasks", 'title: "[Roadmap]"')
            original = original.replace(next(line for line in original.splitlines() if line.startswith("updated:")), "updated: 2020-01-01")
            original = original.replace("---\n\n", "custom: 'It''s [fine]'\n---\n\n", 1)
            path.write_text(original)
            self.assertEqual(run("validate_metadata.py").returncode, 0)
            self.assertEqual(run("repair_metadata.py", "--touch").returncode, 0)
            after = path.read_text()
            result = run("validate_metadata.py")
            self.assertEqual(result.returncode, 0, result.stdout)
            parsed, body, _ = metadata_frontmatter.parse_frontmatter(after)
            self.assertEqual(parsed["title"], "[Roadmap]")
            self.assertEqual(parsed["custom"], "It's [fine]")
            self.assertIn("# Current Tasks", body)
            self.assertEqual(run("repair_metadata.py", "--touch").returncode, 0)
            self.assertEqual(path.read_text(), after)


if __name__ == "__main__":
    unittest.main()
