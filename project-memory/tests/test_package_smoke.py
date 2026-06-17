"""Package-local smoke tests for bundled project-memory scripts."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
METADATA_PATH = SCRIPTS_DIR / "metadata.py"


def load_metadata_module():
    scripts_dir = str(SCRIPTS_DIR)
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)

    spec = importlib.util.spec_from_file_location("metadata", METADATA_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {METADATA_PATH}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PackageSmokeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.metadata = load_metadata_module()

    def test_metadata_module_repairs_missing_required_fields(self) -> None:
        repaired, changed = self.metadata.repair_metadata({}, "TASKS.md")

        self.assertTrue(changed)
        self.assertEqual(repaired["doc_type"], "task_state")
        self.assertEqual(repaired["status"], "active")
        self.assertIn("agent", repaired["audience"])


if __name__ == "__main__":
    unittest.main()
