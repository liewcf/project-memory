# Lightweight GSD-Inspired Project Memory Improvements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add clear next-action and verification guidance to `project-memory` while preserving the current lightweight five-file memory model.

**Architecture:** Keep the existing files, modes, and setup script. Add one small generated `docs/TASKS.md` template improvement, a short `SKILL.md` evidence checklist for existing-project updates, and a matching public README note. Do not add `.planning/`, phases, subagents, runtime config, branch automation, or PR workflow ownership.

**Status:** Original lightweight continuity scope was implemented in `293ef5a` and later hardened on the `codex/lightweight-gsd-project-memory` branch. This file is now a historical implementation plan, not an active task list.

**Tech Stack:** Markdown skill docs, Python standard library setup script, Python `unittest` regression tests, shell validation commands.

---

## Scope

Implement only the lightweight lessons from GSD:

- One clear recommended next action when evidence supports it.
- A simple verification status in `docs/TASKS.md`.
- A short existing-project update checklist so agents inspect real repo evidence before writing durable memory.
- A clear boundary that `project-memory` remains memory maintenance, not a planning or execution framework.

Do not add new memory files, new commands, JSON config, a phase lifecycle, installers, hooks, subagents, model settings, package-manager assumptions, or project-management automation.

## File Structure

- Modify `project-memory/scripts/setup_project_memory.py`: update only the generated `TASKS.md` template.
- Modify `tests/test_setup_project_memory.py`: add one regression test for the generated `TASKS.md` sections.
- Modify `project-memory/SKILL.md`: add concise update/status guidance.
- Modify `README.md`: mirror the public-facing explanation.
- Modify `docs/DECISIONS.md`, `docs/TASKS.md`, and `docs/CHANGELOG_WORK.md` after implementation to keep repo-local project memory accurate.
- Sync `project-memory/` to `/Users/cheonfongliew/.agents/skills/project-memory/` only after local validation passes.

---

### Task 1: Add Regression Coverage For The New Tasks Template

**Files:**
- Modify: `tests/test_setup_project_memory.py`
- Modify: `project-memory/scripts/setup_project_memory.py`

- [x] **Step 1: Write the failing test**

Add this test after `test_creates_docs_directory_and_memory_files` in `tests/test_setup_project_memory.py`:

```python
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
```

- [x] **Step 2: Run the focused test to verify it fails**

Run:

```bash
python3 -m unittest tests.test_setup_project_memory.SetupProjectMemoryTests.test_tasks_template_includes_next_action_and_verification
```

Expected: `FAIL` with an assertion that `## Recommended Next Action` is not found.

- [x] **Step 3: Update the generated `TASKS.md` template**

In `project-memory/scripts/setup_project_memory.py`, replace the `TASKS.md` entry inside `template_for()` with:

```python
        "TASKS.md": """# Tasks

## Recommended Next Action

- Confirm project purpose, build/test commands, and active priorities.

## Current

- [ ] Confirm project purpose, build/test commands, and active priorities.

## Verification

- Not yet verified against repo evidence.

## Blockers

- None recorded.

## Done

- None recorded.
""",
```

- [x] **Step 4: Run the focused test to verify it passes**

Run:

```bash
python3 -m unittest tests.test_setup_project_memory.SetupProjectMemoryTests.test_tasks_template_includes_next_action_and_verification
```

Expected: `OK`.

- [x] **Step 5: Run the full setup test suite**

Run:

```bash
python3 -m unittest discover -s tests -p "test_*.py"
```

Expected: all tests pass.

---

### Task 2: Add Lightweight Update Guidance To The Skill

**Files:**
- Modify: `project-memory/SKILL.md`

- [x] **Step 1: Add next-action and existing-project guidance**

In `project-memory/SKILL.md`, under `## Update`, after the sentence `Use update after meaningful work. Read the relevant project files and current memory before editing.`, add:

```markdown
When updating `docs/TASKS.md`, keep one short `Recommended Next Action` when evidence supports it. Mark whether active work has been verified, is unverified, or needs a specific check. Remove stale next actions after the work lands.

For existing projects with sparse memory or `Unknown` placeholders, inspect the strongest local evidence before writing durable facts: `AGENTS.md`, README or docs, package/build configuration, test files, source layout, recent git history, and changelog-style notes when available. Use only evidence that exists; do not create roadmaps, phases, branches, PRs, or workflow state unless the user asks.
```

- [x] **Step 2: Clarify status output**

In the `## Status` section, replace:

```markdown
- Recommended next action.
```

with:

```markdown
- Recommended next action, including whether it is confirmed by memory or inferred from limited evidence.
```

- [x] **Step 3: Check the skill text**

Run:

```bash
rg -n "Recommended Next Action|Unknown placeholders|workflow state|confirmed by memory" project-memory/SKILL.md
```

Expected: matches for the new update and status guidance.

---

### Task 3: Mirror The Lightweight Boundary In The README

**Files:**
- Modify: `README.md`

- [x] **Step 1: Add the public-facing note**

In `README.md`, after the `## Memory Quality` section, add:

```markdown
## Lightweight Continuity

Good project memory should leave future agents with one clear next action, the current verification state, and facts backed by local evidence.

This skill intentionally does not add phases, roadmaps, subagents, workflow configuration, branch automation, or PR automation. Use it as repo memory, not as a project management system.
```

- [x] **Step 2: Check the README text**

Run:

```bash
rg -n "Lightweight Continuity|one clear next action|not as a project management system" README.md
```

Expected: matches for the new README section.

---

### Task 4: Validate Source Changes And Sync The Installed Skill

**Files:**
- Source: `project-memory/SKILL.md`
- Source: `project-memory/scripts/setup_project_memory.py`
- Installed copy: `/Users/cheonfongliew/.agents/skills/project-memory/`

- [x] **Step 1: Run regression tests**

Run:

```bash
python3 -m unittest discover -s tests -p "test_*.py"
```

Expected: all tests pass.

- [x] **Step 2: Check setup script syntax without local cache writes**

Run:

```bash
PYTHONPYCACHEPREFIX=/tmp/project-memory-pycache python3 -m py_compile project-memory/scripts/setup_project_memory.py
```

Expected: command exits successfully with no syntax errors.

- [x] **Step 3: Sync the verified source skill to the installed profile skill**

Run:

```bash
rsync -a --delete --exclude '__pycache__' project-memory/ /Users/cheonfongliew/.agents/skills/project-memory/
```

Expected: command exits successfully.

- [x] **Step 4: Verify the installed copy matches source**

Run:

```bash
diff -ru --exclude '__pycache__' project-memory/ /Users/cheonfongliew/.agents/skills/project-memory/
```

Expected: no output.

---

### Task 5: Update Repo-Local Project Memory

**Files:**
- Modify: `docs/DECISIONS.md`
- Modify: `docs/TASKS.md`
- Modify: `docs/CHANGELOG_WORK.md`

- [x] **Step 1: Record the product boundary decision**

Add this dated entry to `docs/DECISIONS.md`:

```markdown
## 2026-05-24

- Keep GSD-inspired improvements lightweight: add next-action, verification, and existing-project evidence guidance without adding `.planning/`, phases, subagents, runtime config, branch automation, or PR workflow ownership.
```

- [x] **Step 2: Refresh current task state**

Update `docs/TASKS.md` so the current section reflects no open implementation work after validation:

```markdown
# Tasks

## Recommended Next Action

- None recorded.

## Current

- None recorded.

## Verification

- Latest source changes should be verified with `python3 -m unittest discover -s tests -p "test_*.py"`, `PYTHONPYCACHEPREFIX=/tmp/project-memory-pycache python3 -m py_compile project-memory/scripts/setup_project_memory.py`, and installed-copy `diff -ru --exclude '__pycache__'` after syncing.

## Blockers

- None recorded.

## Done

- [x] Created the `project-memory` skill source package.
- [x] Installed the skill to `~/.agents/skills/project-memory/`.
- [x] Validated `$project-memory setup` support through `SKILL.md`, `openai.yaml`, syntax parsing, and a two-run temp-repo setup check.
- [x] Initialized project memory files in this workspace.
- [x] Prepared the skill source package for GitHub publication with README, MIT license, `.gitignore`, regression tests, and validation notes.
- [x] Initialized git, created the GitHub repository, committed the publish-ready files, and pushed `main`.
- [x] Used `$project-memory status`, `review`, `repair`, and `compact` in real projects as needed and refined the skill if repeated gaps appeared.
- [x] Planned and implemented the move from root memory docs to `docs/`, preserving root `AGENTS.md` as the pointer file.
- [x] Synced the verified `docs/` memory convention update into the installed profile skill at `~/.agents/skills/project-memory/`.
- [x] Added lightweight GSD-inspired next-action, verification, and existing-project evidence guidance without expanding the skill into a workflow framework.
```

- [x] **Step 3: Add the work changelog entry**

Add this dated entry to the top of `docs/CHANGELOG_WORK.md`:

```markdown
## 2026-05-24

- Added generated `docs/TASKS.md` template sections for one recommended next action and verification state.
- Updated `project-memory/SKILL.md` with lightweight existing-project evidence guidance and a clear boundary against adding GSD-style workflow ownership.
- Mirrored the lightweight continuity guidance in `README.md`.
- Verified with unittest, `py_compile`, and installed-copy sync comparison.
```

- [x] **Step 4: Check memory references**

Run:

```bash
rg -n "GSD-inspired|Recommended Next Action|Verification|Lightweight" docs/DECISIONS.md docs/TASKS.md docs/CHANGELOG_WORK.md
```

Expected: matches in all three files.

---

### Task 6: Final Review And Commit

**Files:**
- Review all modified files.

- [x] **Step 1: Review the final diff**

Run:

```bash
git diff -- project-memory/SKILL.md project-memory/scripts/setup_project_memory.py tests/test_setup_project_memory.py README.md docs/DECISIONS.md docs/TASKS.md docs/CHANGELOG_WORK.md
```

Expected: diff contains only the lightweight next-action, verification, existing-project evidence, README, tests, and repo-memory updates described in this plan.

- [x] **Step 2: Check worktree status**

Run:

```bash
git status --short
```

Expected: only the planned files are modified, plus this plan file if it has not been committed separately.
The repo-local memory files under `docs/PROJECT_CONTEXT.md`, `docs/DECISIONS.md`, `docs/TASKS.md`, and `docs/CHANGELOG_WORK.md` are intentionally ignored for public packaging; do not force-add them unless the user explicitly changes that packaging boundary.

- [x] **Step 3: Commit the implementation**

Run:

```bash
git add project-memory/SKILL.md project-memory/scripts/setup_project_memory.py tests/test_setup_project_memory.py README.md docs/superpowers/plans/2026-05-24-lightweight-gsd-inspired-project-memory-improvements.md
git commit -m "Improve project-memory continuity guidance"
```

Expected: commit succeeds.

## Self-Review

- Spec coverage: The plan covers next action, verification state, existing-project evidence checks, README mirroring, validation, installed-skill sync, and repo-local memory updates.
- Placeholder scan: The plan contains concrete file paths, exact text, exact commands, and expected outcomes.
- Scope check: The plan preserves the five-file memory model and avoids GSD-style workflow expansion.
