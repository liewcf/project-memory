"""Regression tests for the project-memory setup script."""

from __future__ import annotations

import importlib.util
import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "project-memory" / "scripts" / "setup_project_memory.py"


def load_setup_module():
    spec = importlib.util.spec_from_file_location("setup_project_memory", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {SCRIPT_PATH}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SetupProjectMemoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.module = load_setup_module()
        self.previous_cwd = Path.cwd()
        self.temp_dir = tempfile.TemporaryDirectory()
        os.chdir(self.temp_dir.name)

    def tearDown(self) -> None:
        os.chdir(self.previous_cwd)
        self.temp_dir.cleanup()

    def run_setup(self) -> int:
        with redirect_stdout(io.StringIO()):
            return self.module.main()

    def test_creates_docs_directory_and_memory_files(self) -> None:
        self.assertEqual(self.run_setup(), 0)

        self.assertTrue(Path("docs").exists(), "docs/ directory should be created")

        for filename in self.module.MEMORY_FILES:
            with self.subTest(filename=filename):
                path = Path("docs") / filename
                self.assertTrue(path.exists(), f"docs/{filename} should be created")
                self.assertTrue(path.read_text(encoding="utf-8").strip())

    def test_tasks_template_includes_next_action_and_verification(self) -> None:
        self.assertEqual(self.run_setup(), 0)

        tasks = (Path("docs") / "TASKS.md").read_text(encoding="utf-8")
        self.assertIn("## Recommended Next Action", tasks)
        self.assertIn(
            "- Confirm project purpose, build/test commands, and active priorities.",
            tasks,
        )
        self.assertIn("## Verification", tasks)
        self.assertIn("- Not yet verified against repo evidence.", tasks)

    def test_second_run_does_not_duplicate_agents_requirement(self) -> None:
        self.assertEqual(self.run_setup(), 0)
        self.assertEqual(self.run_setup(), 0)

        agents = Path("AGENTS.md").read_text(encoding="utf-8")
        self.assertEqual(agents.count(self.module.AGENTS_REQUIREMENT_HEADING), 1)

    def test_existing_agents_content_is_preserved(self) -> None:
        Path("AGENTS.md").write_text(
            "# Existing Agent Notes\n\nKeep the local build command documented.\n",
            encoding="utf-8",
        )

        self.assertEqual(self.run_setup(), 0)

        agents = Path("AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("Keep the local build command documented.", agents)
        self.assertIn(self.module.AGENTS_REQUIREMENT_HEADING, agents)

    def test_existing_root_path_agents_requirement_is_updated(self) -> None:
        Path("AGENTS.md").write_text(
            """# Existing Agent Notes

Keep the local build command documented.

## Project Memory Requirement

- `PROJECT_CONTEXT.md` for stable project facts.
- `DECISIONS.md` for dated technical or product decisions.
- `TASKS.md` for current tasks.
- `CHANGELOG_WORK.md` for dated notes.

## Other Notes

- Preserve this section.
""",
            encoding="utf-8",
        )

        self.assertEqual(self.run_setup(), 0)

        agents = Path("AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("Keep the local build command documented.", agents)
        self.assertIn("## Other Notes", agents)
        self.assertIn("docs/PROJECT_CONTEXT.md", agents)
        self.assertIn("docs/DECISIONS.md", agents)
        self.assertIn("docs/TASKS.md", agents)
        self.assertIn("docs/CHANGELOG_WORK.md", agents)
        self.assertIn("\n\n## Other Notes", agents)
        self.assertEqual(agents.count(self.module.AGENTS_REQUIREMENT_HEADING), 1)

    def test_migrates_legacy_root_files_to_docs(self) -> None:
        legacy_files = ["PROJECT_CONTEXT.md", "DECISIONS.md", "TASKS.md", "CHANGELOG_WORK.md"]
        for filename in legacy_files:
            Path(filename).write_text(f"# Legacy {filename}\n\nLegacy content.\n", encoding="utf-8")

        self.assertEqual(self.run_setup(), 0)

        docs_dir = Path("docs")
        for filename in legacy_files:
            with self.subTest(filename=filename):
                legacy_path = Path(filename)
                docs_path = docs_dir / filename
                self.assertFalse(legacy_path.exists(), f"Root {filename} should be migrated")
                self.assertTrue(docs_path.exists(), f"docs/{filename} should exist after migration")
                self.assertIn(f"Legacy {filename}", docs_path.read_text(encoding="utf-8"))

    def test_does_not_overwrite_existing_docs_files(self) -> None:
        docs_dir = Path("docs")
        docs_dir.mkdir(exist_ok=True)
        (docs_dir / "PROJECT_CONTEXT.md").write_text(
            "# Project Context\n\nExisting docs content.\n", encoding="utf-8"
        )

        self.assertEqual(self.run_setup(), 0)

        project_context = (docs_dir / "PROJECT_CONTEXT.md").read_text(encoding="utf-8")
        self.assertIn("Existing docs content.", project_context)
        self.assertNotIn("Unknown.", project_context)


if __name__ == "__main__":
    unittest.main()
