---
name: project-memory
description: Use when initializing, updating, reviewing, repairing, compacting, or summarizing repo-level project memory files for Codex across software projects.
---

# Project Memory

Use this skill to set up and maintain concise repo-level memory for Codex sessions. It is generic for software projects and repositories; do not assume WordPress or any specific framework unless the project evidence supports it.

## Memory Files

Maintain these files in the project root:

- `AGENTS.md`: short practical instructions for future agents.
- `docs/PROJECT_CONTEXT.md`: stable facts about the project, architecture, workflows, and constraints.
- `docs/DECISIONS.md`: dated append-only technical or product decisions.
- `docs/TASKS.md`: current tasks, blockers, and next actions.
- `docs/CHANGELOG_WORK.md`: dated append-only work log for files, behavior, docs, config, dependencies, and tooling changes.

Never store secrets, passwords, API keys, private tokens, credentials, database dumps, or sensitive personal data in project memory.

## Memory Quality Bar

Project memory is guidance, not the source of truth. Keep only facts that are stable, meaningful, and likely to affect future implementation decisions.

Do not record temporary task progress, obvious implementation details, one-off debugging notes, routine changes, raw command output, secrets, credentials, or private user data.

When memory conflicts with a higher-authority source, follow the higher-authority source and update memory if the correction is durable. Authority order:

1. Current user instruction.
2. Current spec or task requirements.
3. Existing code and tests.
4. Project memory.
5. General best practices.

## Completion Memory Check

At task wrap-up, decide whether project memory needs an update.

Run `$project-memory update` only when durable project context changed:

- Architecture, workflow, commands, or constraints.
- Important decisions, product rules, or accepted spec deviations.
- Current task state, blockers, verification state, or next action.
- Durable open questions that affect future implementation.

Skip the update for trivial edits, routine formatting, failed experiments with no durable lesson, raw command output, or changes with no future value.

If no update is needed, say so briefly in the wrap-up.

## Mode Selection

Infer the mode from the user request when possible. Explicit commands such as `$project-memory setup`, `$project-memory update`, `$project-memory review`, `$project-memory status`, `$project-memory repair`, and `$project-memory compact` map directly to the matching mode.

If the mode is unclear:

- Use `status` for "what is going on?", "summarize this project", or "catch me up".
- Use `update` after meaningful work or wrap-up requests.
- Use `review` for audits, quality checks, or "is this memory good?".
- Use `setup` for initialization or missing memory files.
- Use `repair` for broken structure or content in the wrong file.
- Use `compact` for long, noisy, stale, or hard-to-scan memory files.

## Setup

For `$project-memory setup`, run the bundled script from the repo root:

```bash
python3 ~/.agents/skills/project-memory/scripts/setup_project_memory.py
```

The script creates missing memory files, preserves existing files, and adds or refreshes the `AGENTS.md` project memory requirement when needed.

Setup only initializes the memory structure. It does not infer or populate project-specific facts from repository files, docs, configuration, or history.

If setup runs in an existing project with meaningful source files, docs, configuration, or history, recommend `$project-memory update` next. If the user asked to initialize memory for an existing project or to set up and populate memory, run setup first, then run update in the same turn unless they explicitly asked for setup only.

After running setup, inspect the output and mention which files were created, updated, already existed, or were unchanged.

## Update

Use `update` after meaningful work. Run the completion memory check first during task wrap-up. If an update is needed, read the relevant project files and current memory before editing.

When updating `docs/TASKS.md`, keep one short `Recommended Next Action` when evidence supports it. Mark whether active work has been verified, is unverified, or needs a specific check. Remove stale next actions after the work lands.

For existing projects with sparse memory or `Unknown` placeholders, inspect the strongest local evidence before writing durable facts: `AGENTS.md`, README or docs, package/build configuration, test files, source layout, recent git history, and changelog-style notes when available. Use only evidence that exists; do not create roadmaps, phases, branches, PRs, or workflow state unless the user asks.

Update only what changed:

- `docs/TASKS.md`: task status, blockers, next actions, owners, or follow-up state.
- `docs/CHANGELOG_WORK.md`: dated entries for changed files, behavior, config, dependencies, documentation, tooling, tests, or verification.
- `docs/DECISIONS.md`: important technical or product decisions, including rationale and date.
- `docs/PROJECT_CONTEXT.md`: stable project facts that changed or were newly discovered.
- `AGENTS.md`: only when explicitly asked or when a recurring rule should become permanent.

Update memory when a durable convention, design decision, product rule, architecture constraint, spec deviation, validation requirement, or open question is discovered. Avoid turning `docs/TASKS.md` or `docs/CHANGELOG_WORK.md` into a running transcript.

Prefer concise dated append-only entries for `docs/DECISIONS.md` and `docs/CHANGELOG_WORK.md`. Keep claims factual and evidence-based.

## Compaction Check

After `update`, `review`, or `repair`, briefly assess whether the memory files are becoming noisy, stale, repetitive, or hard to scan.

Do not automatically run `compact` as a hidden follow-up. If compaction looks useful:

- Mention that compaction is recommended.
- Explain the reason in one sentence.
- Ask before compacting unless the user explicitly requested automatic cleanup or `$project-memory compact`.

Recommend compacting when:

- `docs/TASKS.md` mixes many completed or stale items with current work.
- `docs/CHANGELOG_WORK.md` has excessive old detail that obscures recent entries.
- `docs/PROJECT_CONTEXT.md` repeats facts or carries outdated context beside current facts.
- `docs/DECISIONS.md` includes duplicated rationale or exploratory notes that should be summarized.
- A future Codex session would need to read too much to continue safely.

When the user asks for `$project-memory compact`, perform the compaction directly.

## Review

Use `review` to inspect the five memory files without rewriting them by default. Report:

- Missing files.
- Stale sections.
- Duplicated content.
- Overly long content.
- Vague or unhelpful notes.
- Suggested cleanup.

For drift-prone claims such as branch sync, CI presence, published state, or current commands, verify cheap local evidence before reporting them as current.

Do not rewrite everything unless the user asks for edits.

## Status

Use `status` to read the memory files and summarize:

- What the project is.
- Current tasks.
- Recent work.
- Important decisions.
- Blockers or risks.
- Recommended next action, including whether it is confirmed by memory or inferred from limited evidence.

Be clear when a fact is absent, stale, or inferred from limited memory.
Verify cheap local evidence before presenting drift-prone operational facts as current.

## Repair

Use `repair` to fix structural problems while preserving history:

- Normalize headings.
- Move content to the correct file.
- Remove duplicate sections.
- Preserve historical notes.
- Keep `AGENTS.md` short and practical.

Do not silently delete historical context. If content is obsolete but potentially useful, move it to an archive section or mark it as historical.

## Compact

Use `compact` when memory files are noisy or too long:

- Keep important current facts.
- Preserve major decisions.
- Preserve recent changelog entries.
- Archive excessive old detail into an archive section.
- Keep `docs/TASKS.md` easy to scan.

Prefer reducing repetition over removing information. Keep enough context for a future Codex session to continue safely.

## Editing Rules

- Preserve existing useful content.
- Do not overwrite user-authored project memory wholesale.
- Revise existing entries instead of adding duplicate facts.
- Use dated entries where history matters.
- Keep updates concise and factual.
- Separate confirmed facts from assumptions.
- Label inferred facts with source or confidence when useful.
- Avoid project-specific framework claims unless verified from repo evidence.
