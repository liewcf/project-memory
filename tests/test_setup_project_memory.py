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
SKILL_PATH = ROOT / "project-memory" / "SKILL.md"
MODE_REFERENCE_PATH = ROOT / "project-memory" / "references" / "modes.md"
README_PATH = ROOT / "README.md"
OPENAI_YAML_PATH = ROOT / "project-memory" / "agents" / "openai.yaml"


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

    def run_setup_with_output(self) -> tuple[int, str]:
        output = io.StringIO()
        with redirect_stdout(output):
            result = self.module.main()
        return result, output.getvalue()

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
            "- Confirm project purpose, key workflows, review checks, and active priorities.",
            tasks,
        )
        self.assertIn("## Verification", tasks)
        self.assertIn("- Not yet verified against project evidence.", tasks)

    def test_project_context_template_is_generic(self) -> None:
        self.assertEqual(self.run_setup(), 0)

        project_context = (Path("docs") / "PROJECT_CONTEXT.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("## Project Structure", project_context)
        self.assertIn("## Key Workflows", project_context)
        self.assertIn("- Important commands or checks: Unknown.", project_context)
        self.assertIn("- Review method: Unknown.", project_context)
        self.assertIn("- Acceptance criteria: Unknown.", project_context)
        self.assertNotIn("## Architecture", project_context)
        self.assertNotIn("## Development Workflow", project_context)
        self.assertNotIn("Package manager:", project_context)
        self.assertNotIn("Build command:", project_context)
        self.assertNotIn("Test command:", project_context)
        self.assertNotIn("Run command:", project_context)

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
        self.assertIn("project, product, technical, process, or content decisions", agents)
        self.assertIn("docs, assets, behavior, deliverables", agents)
        self.assertIn("\n\n## Other Notes", agents)
        self.assertEqual(agents.count(self.module.AGENTS_REQUIREMENT_HEADING), 1)

    def test_existing_docs_path_agents_requirement_missing_safety_is_updated(self) -> None:
        Path("AGENTS.md").write_text(
            """# Existing Agent Notes

Keep the local build command documented.

## Project Memory Requirement

- `docs/PROJECT_CONTEXT.md` for stable project facts.
- `docs/DECISIONS.md` for dated technical or product decisions.
- `docs/TASKS.md` for current tasks.
- `docs/CHANGELOG_WORK.md` for dated notes.

## Other Notes

- Preserve this section.
""",
            encoding="utf-8",
        )

        result, output = self.run_setup_with_output()

        agents = Path("AGENTS.md").read_text(encoding="utf-8")
        self.assertEqual(result, 0)
        self.assertIn("Do not store secrets", agents)
        self.assertIn("project folders or repositories", agents)
        self.assertIn("## Other Notes", agents)
        self.assertIn("Updated: AGENTS.md", output)
        self.assertEqual(agents.count(self.module.AGENTS_REQUIREMENT_HEADING), 1)

    def test_existing_old_canonical_agents_requirement_is_updated(self) -> None:
        Path("AGENTS.md").write_text(
            """# Existing Agent Notes

Keep the local build command documented.

## Project Memory Requirement

Keep these repo-level memory files accurate and concise when work changes project context:

- `docs/PROJECT_CONTEXT.md` for stable project facts, architecture, workflows, and constraints.
- `docs/DECISIONS.md` for dated technical or product decisions and rationale.
- `docs/TASKS.md` for current tasks, blockers, and next actions.
- `docs/CHANGELOG_WORK.md` for dated notes on changed files, behavior, docs,
  config, dependencies, tooling, tests, and verification.

Do not store secrets, credentials, API keys, private tokens, database dumps,
or sensitive personal data in project memory.

## Other Notes

- Preserve this section.
""",
            encoding="utf-8",
        )

        result, output = self.run_setup_with_output()

        agents = Path("AGENTS.md").read_text(encoding="utf-8")
        self.assertEqual(result, 0)
        self.assertIn("Updated: AGENTS.md", output)
        self.assertIn("project folders or repositories", agents)
        self.assertIn("project, product, technical, process, or content decisions", agents)
        self.assertIn("docs, assets, behavior, deliverables", agents)
        self.assertNotIn("repo-level memory files", agents)
        self.assertNotIn("architecture, workflows", agents)
        self.assertIn("## Other Notes", agents)
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

    def test_reports_legacy_root_files_left_when_docs_versions_exist(self) -> None:
        docs_dir = Path("docs")
        docs_dir.mkdir(exist_ok=True)
        (docs_dir / "TASKS.md").write_text("# Tasks\n\nDocs content.\n", encoding="utf-8")
        Path("TASKS.md").write_text("# Tasks\n\nRoot legacy content.\n", encoding="utf-8")

        result, output = self.run_setup_with_output()

        self.assertEqual(result, 0)
        self.assertTrue(Path("TASKS.md").exists())
        self.assertIn("Docs content.", (docs_dir / "TASKS.md").read_text(encoding="utf-8"))
        self.assertIn("Legacy root files left in place: TASKS.md", output)

    def test_rejects_symlinked_agents_file(self) -> None:
        outside_dir = Path(self.temp_dir.name) / "outside"
        outside_dir.mkdir()
        outside_agents = outside_dir / "target_agents.md"
        outside_agents.write_text("# Outside file\n", encoding="utf-8")
        Path("AGENTS.md").symlink_to(outside_agents)

        with self.assertRaisesRegex(RuntimeError, "symlinked project memory path"):
            self.run_setup()

        self.assertEqual(outside_agents.read_text(encoding="utf-8"), "# Outside file\n")

    def test_rejects_symlinked_docs_directory(self) -> None:
        outside_docs = Path(self.temp_dir.name) / "outside-docs"
        outside_docs.mkdir()
        Path("docs").symlink_to(outside_docs)

        with self.assertRaisesRegex(RuntimeError, "symlinked project memory path"):
            self.run_setup()

        self.assertEqual(list(outside_docs.iterdir()), [])

    def test_rejects_broken_docs_file_symlink(self) -> None:
        docs_dir = Path("docs")
        docs_dir.mkdir()
        outside_target = Path(self.temp_dir.name) / "outside-project-context.md"
        (docs_dir / "PROJECT_CONTEXT.md").symlink_to(outside_target)

        with self.assertRaisesRegex(RuntimeError, "symlinked project memory path"):
            self.run_setup()

        self.assertFalse(outside_target.exists())


class SkillInstructionTests(unittest.TestCase):
    def test_completion_memory_check_guidance_is_documented(self) -> None:
        skill = SKILL_PATH.read_text(encoding="utf-8")
        readme = README_PATH.read_text(encoding="utf-8")
        openai_yaml = OPENAI_YAML_PATH.read_text(encoding="utf-8")

        self.assertIn("## Completion Memory Check", skill)
        self.assertIn("durable project context changed", skill)
        self.assertIn("trivial edits, routine formatting", skill)
        self.assertIn("If no update is needed, say so briefly", skill)
        self.assertIn("Run the completion memory check first", skill)
        self.assertIn("completion memory check", readme)
        self.assertIn("only if durable project context changed", readme)
        self.assertIn(
            'default_prompt: "Use $project-memory to set up, update, or review project memory."',
            openai_yaml,
        )

    def test_worked_examples_cover_recurring_edge_cases(self) -> None:
        required_phrases = [
            "## Worked Examples",
            "Do not run `$project-memory update`",
            "Do not inspect other project threads",
            "Other threads can be stale, private, or about a different checkout.",
            "Keep current items in `docs/TASKS.md` as bullets",
        ]

        for path in [SKILL_PATH, README_PATH]:
            content = path.read_text(encoding="utf-8")
            with self.subTest(path=path):
                for phrase in required_phrases:
                    self.assertIn(phrase, content)

    def test_skill_defers_mode_details_to_reference(self) -> None:
        skill = SKILL_PATH.read_text(encoding="utf-8")
        mode_reference = MODE_REFERENCE_PATH.read_text(encoding="utf-8")

        self.assertIn("references/modes.md", skill)
        self.assertLessEqual(len(skill.splitlines()), 100)

        for heading in [
            "## Setup",
            "## Update",
            "## Review",
            "## Status",
            "## Repair",
            "## Compact",
        ]:
            with self.subTest(heading=heading):
                self.assertIn(heading, mode_reference)

    def test_agents_update_rule_promotes_only_durable_guidance(self) -> None:
        mode_reference = MODE_REFERENCE_PATH.read_text(encoding="utf-8")

        for phrase in [
            "### AGENTS.md Updates",
            "quick check for whether `AGENTS.md` needs new or revised",
            "Edit `AGENTS.md` only when current evidence supports",
            "Do not do a deep history review for every routine",
            "Promote only guidance future agents should act on repeatedly",
            "Do not add task progress, detailed history, raw command output",
            "Do not invent package managers, frameworks, CI, deploy",
            "confirm it still matches current files",
        ]:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, mode_reference)

    def test_setup_command_uses_portable_skill_dir_placeholder(self) -> None:
        portable_command = "python3 <project-memory skill dir>/scripts/setup_project_memory.py"
        hardcoded_command = "python3 ~/.agents/skills/project-memory/scripts/setup_project_memory.py"

        for path in [SKILL_PATH, README_PATH]:
            content = path.read_text(encoding="utf-8")
            with self.subTest(path=path):
                self.assertIn(portable_command, content)
                self.assertNotIn(hardcoded_command, content)


if __name__ == "__main__":
    unittest.main()
