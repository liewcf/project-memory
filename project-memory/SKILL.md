---
name: project-memory
description: Use when setting up, updating, reviewing, repairing, compacting, or summarizing Codex project memory files.
---

# Project Memory

Use this skill to keep concise project-level memory for Codex. It is generic for
project folders and repositories. Do not assume a framework, toolchain, domain, or
deployment setup unless current project evidence supports it.

For detailed mode rules after you choose a mode, read
`references/modes.md`.

## Memory Files

Maintain these files in the project root:

- `AGENTS.md`: short practical instructions for future agents.
- `docs/PROJECT_CONTEXT.md`: stable project facts, structure, workflows, resources, and constraints.
- `docs/DECISIONS.md`: dated project, product, technical, process, or content decisions.
- `docs/TASKS.md`: current tasks, blockers, verification state, and next actions.
- `docs/CHANGELOG_WORK.md`: dated notes on changed files, docs, assets, behavior, deliverables, process, tooling, checks, and verification.

Never store secrets, passwords, API keys, private tokens, credentials, database
dumps, or sensitive personal data.

## Mode Selection

Infer the mode from the user request:

- `setup`: initialize missing memory files or migrate legacy root memory files.
- `update`: update memory after meaningful work or when durable context changed.
- `review`: inspect memory quality without rewriting by default.
- `status`: summarize project memory and the recommended next action.
- `repair`: fix broken or duplicated memory structure while preserving history.
- `compact`: shorten noisy, stale, or hard-to-scan memory files.

If the mode is unclear, use `status` for catch-up questions, `review` for
quality/audit questions, and `update` for wrap-up after meaningful work.

## Setup

For `$project-memory setup`, resolve the skill directory from this loaded
`SKILL.md` path. Then run this from the target project root:

```bash
python3 <project-memory skill dir>/scripts/setup_project_memory.py
```

The script creates missing memory files, preserves existing files, migrates
legacy root files when safe, and refreshes the `AGENTS.md` memory requirement.
Setup only initializes the memory structure. It does not infer project facts.

After setup, report created, updated, existing, migrated, unchanged, and
left-in-place files. If this is an existing project, recommend or run `update` next
unless the user asked for setup only.

## Completion Memory Check

At task wrap-up, decide whether project memory needs an update. Run
`$project-memory update` only when durable project context changed:

- Structure, workflow, commands, review checks, resources, or constraints.
- Important decisions, product rules, process rules, content rules, or accepted spec deviations.
- Current task state, blockers, verification state, or next action.
- Durable open questions that affect future work.

Skip the update for trivial edits, routine formatting, failed experiments with no
durable lesson, raw command output, or changes with no future value. If no update is needed, say so briefly.

## Update Rules

Run the completion memory check first. If an update is needed, read current
memory plus the strongest cheap evidence: `AGENTS.md`, README or docs, project
files, config, commands/checks, source layout, changelog notes, and recent git
history when present.

Update only what changed. Keep entries concise, dated where history matters, and
evidence-based. Separate confirmed facts from assumptions. Do not create phases,
roadmaps, branches, PRs, or workflow state unless the user asks.

After `update`, `review`, or `repair`, assess whether memory is noisy enough to
recommend `compact`. Do not run compaction automatically unless requested.

## Worked Examples

- No durable change: Do not run `$project-memory update` after a typo fix, routine formatting, a reverted experiment, or work already covered by current memory.
- Other threads: Do not inspect other project threads for `update` unless the user asks or provides them. Other threads can be stale, private, or about a different checkout.
- Current tasks: Keep current items in `docs/TASKS.md` as bullets. Use numbered lists only when order matters.

## Authority And Editing

Project memory is guidance, not the source of truth. Follow higher-authority
sources in this order: current user instruction, current task/spec, current
project files and checks, project memory, then general best practices.

Preserve useful user-authored content. Revise existing entries instead of adding
duplicates. Avoid project-specific framework, tooling, domain, or workflow claims
unless verified from project evidence.
