# Project Memory Skill

A Codex skill for setting up and maintaining concise repo-level memory files across software projects.

The skill gives future coding agents a stable place to find project context, decisions, active tasks, and recent work without relying only on chat history.

## What It Creates

Running setup in a project root creates or updates these files:

- `AGENTS.md`: practical instructions for future agents.
- `PROJECT_CONTEXT.md`: stable project facts, architecture, workflows, and constraints.
- `DECISIONS.md`: dated technical or product decisions and rationale.
- `TASKS.md`: current tasks, blockers, and next actions.
- `CHANGELOG_WORK.md`: dated work log for changed files, behavior, docs, config, dependencies, tooling, tests, and verification.

Existing files are preserved. The setup script only appends the project memory requirement to `AGENTS.md` when similar guidance is missing.

## Install

Copy the `project-memory` folder into your Codex skills directory:

```bash
mkdir -p ~/.agents/skills
cp -R project-memory ~/.agents/skills/
```

Restart Codex or open a new session if the skill does not appear immediately.

## Usage

From a software project root, ask Codex:

```text
$project-memory setup
```

Other supported modes:

- `$project-memory status`: summarize current project memory.
- `$project-memory update`: update memory after meaningful work.
- `$project-memory review`: inspect memory quality without rewriting by default.
- `$project-memory repair`: normalize broken or duplicated memory structure.
- `$project-memory compact`: shorten noisy or stale memory while preserving useful history.

## Manual Setup Script

After installing the skill, you can run the bundled setup script directly:

```bash
python3 ~/.agents/skills/project-memory/scripts/setup_project_memory.py
```

Run it from the root of the project where you want memory files created.

## Validate

Run the regression tests:

```bash
python3 -m unittest discover -s tests -p "test_*.py"
```

Check the setup script parses:

```bash
python3 -m py_compile project-memory/scripts/setup_project_memory.py
```

Run an idempotency smoke test:

```bash
tmpdir="$(mktemp -d)"
(
  cd "$tmpdir"
  python3 /path/to/liewcf-project-memory/project-memory/scripts/setup_project_memory.py
  python3 /path/to/liewcf-project-memory/project-memory/scripts/setup_project_memory.py
)
```

The first run should create the memory files. The second run should not duplicate the `AGENTS.md` project memory requirement.

## Repository Layout

```text
project-memory/
  SKILL.md
  agents/openai.yaml
  scripts/setup_project_memory.py
tests/
  test_setup_project_memory.py
.github/workflows/ci.yml
```

The root-level `PROJECT_CONTEXT.md`, `DECISIONS.md`, `TASKS.md`, and `CHANGELOG_WORK.md` files describe development history for this source package.

## Safety

Do not store secrets, credentials, API keys, private tokens, database dumps, or sensitive personal data in project memory files.

## License

MIT. See `LICENSE`.
