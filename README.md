# Project Memory Skill

A Codex skill for setting up and maintaining concise project-level memory files across project folders and repositories.

The skill gives future Codex sessions a stable place to find project context, decisions, active tasks, and recent work without relying only on chat history. It supports software, writing, research, design, operations, client work, and other structured projects.

## What It Creates

Running setup in a project root creates or updates these files:

- `AGENTS.md`: practical instructions for future agents.
- `docs/PROJECT_CONTEXT.md`: stable project facts, structure, workflows, resources, and constraints.
- `docs/DECISIONS.md`: dated project, product, technical, process, or content decisions and rationale.
- `docs/TASKS.md`: current tasks, blockers, and next actions.
- `docs/CHANGELOG_WORK.md`: dated work log for changed files, docs, assets, behavior, deliverables, process, tooling, checks, and verification.

Existing files are preserved. The setup script adds or refreshes the project memory requirement in `AGENTS.md` when needed.

Setup initializes the memory structure only; it does not populate project-specific facts from project evidence. In an existing project, run `$project-memory update` after setup to fill in concise facts, tasks, decisions, and recent work.

## Install

Copy the `project-memory` folder into your Codex skills directory:

```bash
mkdir -p ~/.agents/skills
cp -R project-memory ~/.agents/skills/
```

To refresh an existing installed copy from this checkout:

```bash
rsync -a --delete --exclude '__pycache__' project-memory/ ~/.agents/skills/project-memory/
```

Restart Codex or open a new session if the skill does not appear immediately.

## Usage

From a project folder or repository root, ask Codex:

```text
$project-memory setup
```

Other supported modes:

- `$project-memory status`: summarize current project memory.
- `$project-memory update`: update memory after meaningful work when durable project context changed.
- `$project-memory review`: inspect memory quality without rewriting by default.
- `$project-memory repair`: normalize broken or duplicated memory structure.
- `$project-memory compact`: shorten noisy or stale memory while preserving useful history.

## Example Workflow

1. Install the skill.
2. Run `$project-memory setup` in the project root.
3. If this is an existing project, run `$project-memory update` to populate memory from current project evidence.
4. Do project work.
5. At wrap-up, run a completion memory check; run `$project-memory update` only if durable project context changed.
6. Future agents read the memory files before continuing work.

## Memory Quality

Project memory is guidance, not the source of truth. Keep only stable, meaningful facts that are likely to affect future work.

Good memory entries include durable conventions, design decisions, product or domain rules, process rules, content rules, structure constraints, accepted spec deviations, open questions, and validation requirements.

Avoid recording temporary task progress, obvious implementation details, one-off debugging notes, routine changes, raw command output, secrets, credentials, or private user data. When memory conflicts with the current user instruction, current spec, current project files, or current checks, follow the current higher-authority source and update memory only if the correction is durable.

## Lightweight Continuity

Good project memory should leave future agents with one clear next action, the current verification state, and facts backed by local evidence.

At task wrap-up, run a completion memory check. Update memory only if durable project context changed, such as decisions, commands, constraints, task state, blockers, verification state, or next action.

This skill intentionally does not add phases, roadmaps, subagents, workflow configuration, branch automation, or PR automation. Use it as project memory, not as a project management system.

## Worked Examples

- No durable change: Do not run `$project-memory update` after task completion when the work was a typo fix, routine formatting, a reverted experiment, or already covered by current memory. Say that no update was needed.
- Other threads: Do not inspect other project threads for `update` unless the user asks for that context or provides it directly. Other threads can be stale, private, or about a different checkout. Use the current repo, current task, local files, current memory, and cheap git evidence.
- Current tasks: Keep current items in `docs/TASKS.md` as bullets. Use numbered lists only when the order itself matters, such as a step-by-step next action.

## Manual Setup Script

After installing the skill, you can run the bundled setup script directly. Replace `<project-memory skill dir>` with the installed `project-memory` skill folder.

```bash
python3 <project-memory skill dir>/scripts/setup_project_memory.py
```

Run it from the root of the project where you want memory files created.

## Validate

Run the regression tests:

```bash
python3 -m unittest discover -s tests -p "test_*.py"
```

Check the setup script parses:

```bash
PYTHONPYCACHEPREFIX=/tmp/project-memory-pycache python3 -m py_compile project-memory/scripts/setup_project_memory.py
```

## Metadata Hygiene

Memory files under `docs/` carry Project Memory Metadata v1 YAML frontmatter (title, doc_type, status, dates, tags, audience, related). `AGENTS.md` stays plain Markdown without frontmatter. The Markdown body remains the source of truth.

Validate metadata:

```bash
python3 <project-memory skill dir>/scripts/validate_metadata.py
python3 <project-memory skill dir>/scripts/validate_metadata.py --root /path/to/project
```

Repair metadata:

```bash
python3 <project-memory skill dir>/scripts/repair_metadata.py
python3 <project-memory skill dir>/scripts/repair_metadata.py --touch
python3 <project-memory skill dir>/scripts/repair_metadata.py --root /path/to/project
```

## Repository Layout

```text
project-memory/
  SKILL.md
  agents/openai.yaml
  references/modes.md
  scripts/metadata.py
  scripts/setup_project_memory.py
  scripts/validate_metadata.py
  scripts/repair_metadata.py
tests/
  test_setup_project_memory.py
  test_metadata.py
  test_validate_metadata.py
  test_repair_metadata.py
```

The root-level `AGENTS.md` is the only root project memory file. `docs/PROJECT_CONTEXT.md`, `docs/DECISIONS.md`, `docs/TASKS.md`, and `docs/CHANGELOG_WORK.md` describe development history for this source package.

## Safety

Do not store secrets, credentials, API keys, private tokens, database dumps, or sensitive personal data in project memory files.

## License

MIT. See `LICENSE`.
