# Project Memory Mode Details

Load this file after choosing a `project-memory` mode and only use the sections
needed for the request.

## Setup

- Run the bundled setup script from the target project root.
- Inspect the script output before summarizing.
- Mention files that were created, updated, already existed, migrated, unchanged,
  or left in place.
- If setup runs in an existing project with meaningful files, docs, config,
  assets, source files, or history, recommend `$project-memory update` next.
- If the user asked to set up and populate memory, run setup first, then update
  in the same turn unless they explicitly asked for setup only.

## Update

Use `update` after meaningful work or when project memory is sparse, stale, or
missing durable facts.

Read the relevant project files and current memory before editing. For sparse
memory or `Unknown` placeholders, inspect the strongest local evidence first:
`AGENTS.md`, README or docs, project files, assets, configuration, commands,
review checks, source layout, recent git history, and changelog notes when
available.

Update only what changed:

- `docs/TASKS.md`: task status, blockers, owners, verification state, and one
  short `Recommended Next Action` when evidence supports it.
- `docs/CHANGELOG_WORK.md`: dated entries for changed files, docs, assets,
  behavior, deliverables, process, config, tooling, checks, or verification.
- `docs/DECISIONS.md`: important project, product, technical, process, or
  content decisions with rationale.
- `docs/PROJECT_CONTEXT.md`: stable project facts that changed or were newly
  discovered.
- `AGENTS.md`: only when asked or when a recurring rule should become permanent.

Avoid turning `docs/TASKS.md` or `docs/CHANGELOG_WORK.md` into a transcript.

## Review

Use `review` to inspect the five memory files without rewriting them by default.
Report missing files, stale sections, duplicated content, overly long content,
vague notes, and suggested cleanup.

For drift-prone claims such as branch sync, CI presence, published state,
current commands, or current deliverable status, verify cheap local evidence
before reporting them as current.

## Status

Use `status` to summarize:

- What the project is.
- Current tasks.
- Recent work.
- Important decisions.
- Blockers or risks.
- Recommended next action, including whether it is confirmed by memory or
  inferred from limited evidence.

Be clear when a fact is absent, stale, or inferred.

## Repair

Use `repair` to fix structural problems while preserving history:

- Normalize headings.
- Move content to the correct file.
- Remove duplicate sections.
- Preserve historical notes.
- Keep `AGENTS.md` short and practical.

Do not silently delete historical context. If content is obsolete but possibly
useful, move it to an archive section or mark it historical.

## Compact

Use `compact` when memory files are noisy or too long:

- Keep important current facts.
- Preserve major decisions.
- Preserve recent changelog entries.
- Archive excessive old detail into an archive section.
- Keep `docs/TASKS.md` easy to scan.

Prefer reducing repetition over removing information. Keep enough context for a
future Codex session to continue safely.

Recommend compaction when:

- `docs/TASKS.md` mixes many completed or stale items with current work.
- `docs/CHANGELOG_WORK.md` has old detail that hides recent entries.
- `docs/PROJECT_CONTEXT.md` repeats facts or carries outdated context.
- `docs/DECISIONS.md` has duplicated rationale or exploratory notes.
- A future session would need to read too much to continue safely.
