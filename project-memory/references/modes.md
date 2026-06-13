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
- When creating new docs files, include valid Project Memory Metadata v1
  frontmatter. When migrating legacy files, prepend frontmatter if missing.
  Keep `AGENTS.md` as plain Markdown without frontmatter.

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
- `AGENTS.md`: durable future-agent operating guidance, following the
  `AGENTS.md Updates` rule below.

Avoid turning `docs/TASKS.md` or `docs/CHANGELOG_WORK.md` into a transcript.

When updating a memory file, update the `updated` field in its Project Memory
Metadata v1 frontmatter to the current date when durable content changed.
Preserve existing meaningful metadata fields.

### AGENTS.md Updates

During `update`, do a quick check for whether `AGENTS.md` needs new or revised
future-agent guidance. Edit `AGENTS.md` only when current evidence supports a
durable operating rule.

Start with cheap current evidence: the existing `AGENTS.md`, current memory
files, README or docs, visible config, known commands/checks, source layout, and
recent changelog notes. Use recent git history when it is available and likely
to clarify a durable rule. Do not do a deep history review for every routine
memory update.

Promote only guidance future agents should act on repeatedly:

- currently valid build, test, check, setup, release, or maintenance commands
- source-of-truth files and ownership boundaries
- public/private packaging boundaries
- known pitfalls, blocked paths, or environment constraints
- verification rules such as "do not claim X unless Y exists"

Do not add task progress, detailed history, raw command output, temporary
blockers, stale plans, or one-off notes to `AGENTS.md`. Keep those in the
matching memory docs. Do not invent package managers, frameworks, CI, deploy
commands, or release rules.

Before adding a rule from older history, confirm it still matches current files
or mark it as ambiguous and leave it out. Prefer revising or replacing stale
guidance over adding duplicate guidance.

After editing `AGENTS.md`, verify the edit with readback and, when available,
`git diff -- AGENTS.md` or `git status --short`. In the update report, mention
the `AGENTS.md` change and any ambiguity that affected it.

## Review

Use `review` to inspect the five memory files without rewriting them by default.
Report missing files, stale sections, duplicated content, overly long content,
vague notes, and suggested cleanup.

Check whether docs memory files have valid Project Memory Metadata v1
frontmatter. Do not rewrite automatically during review. Recommend
`$project-memory repair` if metadata is missing or invalid.

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

Repair missing or invalid Project Memory Metadata v1 frontmatter in docs memory
files. Preserve existing Markdown body content. Keep `AGENTS.md` plain Markdown.

Scripts for metadata repair:

```bash
python3 <project-memory skill dir>/scripts/repair_metadata.py
python3 <project-memory skill dir>/scripts/repair_metadata.py --touch
```

Do not silently delete historical context. If content is obsolete but possibly
useful, move it to an archive section or mark it historical.

## Compact

Use `compact` when memory files are noisy or too long:

- Keep important current facts.
- Preserve major decisions.
- Preserve recent changelog entries.
- Archive excessive old detail into an archive section.
- Keep `docs/TASKS.md` easy to scan.

Preserve Project Memory Metadata v1 frontmatter when compacting memory files.
Compact only the Markdown body unless metadata itself is stale or invalid.

Prefer reducing repetition over removing information. Keep enough context for a
future Codex session to continue safely.

Recommend compaction when:

- `docs/TASKS.md` mixes many completed or stale items with current work.
- `docs/CHANGELOG_WORK.md` has old detail that hides recent entries.
- `docs/PROJECT_CONTEXT.md` repeats facts or carries outdated context.
- `docs/DECISIONS.md` has duplicated rationale or exploratory notes.
- A future session would need to read too much to continue safely.
