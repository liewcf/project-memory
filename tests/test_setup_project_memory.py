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

    def test_creates_expected_memory_files(self) -> None:
        self.assertEqual(self.run_setup(), 0)

        for filename in self.module.MEMORY_FILES:
            with self.subTest(filename=filename):
                path = Path(filename)
                self.assertTrue(path.exists(), f"{filename} should be created")
                self.assertTrue(path.read_text(encoding="utf-8").strip())

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


if __name__ == "__main__":
    unittest.main()
