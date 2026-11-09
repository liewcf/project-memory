# Project Memory Skill

An agent skill for setting up and maintaining concise project-level memory files across project folders and repositories, for Codex, Claude, and other coding-agent sessions.

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

Run both shipped unittest suites for a complete check:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p "test_*.py"
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s project-memory/tests -p "test_*.py"
```

Normal discovery includes the 12 checks in `tests/test_linux_metadata.py` on
Linux. They use synthetic files and standard-library ACL/xattr APIs, with no
Docker or extra Python packages required. Other platforms and filesystems
without the required ACL/xattr support report explicit skips. The group-change
check also requires a supplementary group different from the effective group.

Check all bundled scripts parse without writing bytecode into the repository:

```bash
PYTHONPYCACHEPREFIX=/tmp/project-memory-pycache python3 -m py_compile project-memory/scripts/*.py
```

## Metadata Hygiene

Memory files under `docs/` carry Project Memory Metadata v1 YAML frontmatter (title, doc_type, status, dates, tags, audience, related). `AGENTS.md` stays plain Markdown without frontmatter. The Markdown body remains the source of truth.

Metadata v1 intentionally supports only scalar `key: value` fields and indented
`- item` lists. Flow mappings, flow sequences, nested YAML, and other
unsupported frontmatter lines are rejected. Repair skips unsupported
frontmatter instead of silently converting or discarding it.
Repair and validation report unreadable UTF-8 per file, continue with the other
files, and return a nonzero exit status. Repair preserves the unreadable bytes.
Mapping colons require whitespace before a value; bare `key:` fields remain
supported. Lines such as `title:Roadmap` are rejected.

Quoted scalars support JSON-compatible double-quoted escapes and doubled single
quotes. Rendering quotes ambiguous scalar and list-item values; repair reparses
generated metadata and checks the values match before publishing it.
Whitespace-separated inline comments are recognized outside quoted values.
Scalar values remain strings, including quoted boolean, numeric, null and date
spellings. Anchors, aliases, tags, block scalars and unquoted collection or
mapping syntax are rejected in both fields and list items.

Unterminated frontmatter, repeated keys, list items following a scalar, and
changing list indentation are rejected without rewriting the affected file.
Setup checks paths and legacy frontmatter before writing. Migration publishes
the complete docs copy before removing the root copy; a removal failure leaves
both copies for manual reconciliation.

Setup and repair stage each complete file before publishing it. Failed staging
or publication preserves the previous destination. Existing ownership,
permission bits, ACLs and extended attributes are retained through descriptors
on macOS and Linux; failure to preserve metadata stops publication. Atomic
replacement creates a new inode, so hard-linked aliases retain their original
contents. Repair and AGENTS refresh carry the file version captured during
reading into publication and refuse detected intervening edits or replacements.
Changes detected during a read also stop that operation. These are per-file
guarantees, not a transaction across every file or a lock against concurrent writers. See the
[state transition reference](project-memory/references/state-transitions.md).

On macOS, copying metadata replaces the staging file's ACL exactly, clearing
inherited entries that are absent from the source. A source with no ACL remains
without one after replacement or migration.

If a file is published but its temporary hard link cannot be removed, repair
reports `PUBLISHED` with a cleanup warning and the retained temporary name;
setup also reports that publication occurred. Both return a nonzero exit status.
The destination is already saved. A migration keeps its legacy source in this
case, leaving both copies available for reconciliation.

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
  scripts/metadata_defaults.py
  scripts/metadata_frontmatter.py
  scripts/file_metadata.py
  scripts/metadata_repair.py
  scripts/metadata_validation.py
  scripts/path_safety.py
  scripts/setup_project_memory.py
  scripts/validate_metadata.py
  scripts/repair_metadata.py
  tests/test_package_smoke.py
tests/
  test_setup_project_memory.py
  test_metadata.py
  test_validate_metadata.py
  test_repair_metadata.py
  test_linux_metadata.py
```

The root-level `AGENTS.md` is the only root project memory file. `docs/PROJECT_CONTEXT.md`, `docs/DECISIONS.md`, `docs/TASKS.md`, and `docs/CHANGELOG_WORK.md` describe development history for this source package.

## Safety

Do not store secrets, credentials, API keys, private tokens, database dumps, or sensitive personal data in project memory files.

Metadata repair uses descriptor-relative no-follow operations when the runtime
exposes the required POSIX primitives. If those race-safe primitives are
unavailable, repair exits with an explicit error instead of falling back to an
unsafe path-based write.

## License

MIT. See `LICENSE`.
