# Project Memory Skill

A Codex skill for setting up and maintaining concise repo-level memory files across software projects.

The skill gives future coding agents a stable place to find project context, decisions, active tasks, and recent work without relying only on chat history.

## What It Creates

Running setup in a project root creates or updates these files:

- `AGENTS.md`: practical instructions for future agents.
- `docs/PROJECT_CONTEXT.md`: stable project facts, architecture, workflows, and constraints.
- `docs/DECISIONS.md`: dated technical or product decisions and rationale.
- `docs/TASKS.md`: current tasks, blockers, and next actions.
- `docs/CHANGELOG_WORK.md`: dated work log for changed files, behavior, docs, config, dependencies, tooling, tests, and verification.

Existing files are preserved. The setup script adds or refreshes the project memory requirement in `AGENTS.md` when needed.

Setup initializes the memory structure only; it does not populate project-specific facts from repo evidence. In an existing project, run `$project-memory update` after setup to fill in concise facts, tasks, decisions, and recent work.

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

## Example Workflow

1. Install the skill.
2. Run `$project-memory setup` in the project root.
3. If this is an existing project, run `$project-memory update` to populate memory from current repo evidence.
4. Do coding work.
5. Run `$project-memory update` after meaningful changes.
6. Future agents read the memory files before continuing work.

## Memory Quality

Project memory is guidance, not the source of truth. Keep only stable, meaningful facts that are likely to affect future implementation decisions.

Good memory entries include durable conventions, design decisions, product or domain rules, architecture constraints, accepted spec deviations, open questions, and validation requirements.

Avoid recording temporary task progress, obvious implementation details, one-off debugging notes, routine changes, raw command output, secrets, credentials, or private user data. When memory conflicts with the current user instruction, current spec, or current code and tests, follow the current higher-authority source and update memory only if the correction is durable.

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

The root-level `AGENTS.md` is the only root project memory file. `docs/PROJECT_CONTEXT.md`, `docs/DECISIONS.md`, `docs/TASKS.md`, and `docs/CHANGELOG_WORK.md` describe development history for this source package.

## Safety

Do not store secrets, credentials, API keys, private tokens, database dumps, or sensitive personal data in project memory files.

## License

MIT. See `LICENSE`.
