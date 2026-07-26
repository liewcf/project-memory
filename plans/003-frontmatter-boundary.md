# Plan 003: Make the frontmatter boundary strict and truthful

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving on. If
> anything in the STOP conditions section occurs, stop and report. Touch only
> the files listed in Scope. Do not update `plans/README.md`; the reviewer
> maintains that index.

> **Drift check (run first)**: `git diff --stat 0766747..HEAD -- project-memory/scripts/metadata_frontmatter.py README.md tests/test_metadata.py tests/test_repair_metadata.py`

## Status

- **Priority**: P1
- **Effort**: M
- **Risk**: MED
- **Depends on**: `plans/001-verification-baseline.md`
- **Category**: correctness, tech-debt, docs
- **Planned at**: commit `0766747`, 2026-07-14
- **Execution status**: DONE — verified in the 2026-07-27 worktree

## Why this matters

The parser treats any text beginning with `---` as frontmatter, even when the
opening line is `---not-a-delimiter`. When repair then adds missing metadata, it
can rebuild the file without preserving the text that was misread as metadata.
The parser also silently ignores unsupported top-level lines while the README
describes the format generally as YAML. This plan makes malformed input fail
closed and documents the intentionally small YAML subset.

## Current state

- `project-memory/scripts/metadata_frontmatter.py:13-30` uses
  `stripped.startswith("---")`, then searches for a closing delimiter.
- `project-memory/scripts/metadata_frontmatter.py:33-60` parses recognized
  pairs and list items but does not reject every unrecognized non-blank line.
- `project-memory/scripts/metadata_frontmatter.py:93-106` rejects flow and
  nested YAML but does not expose that contract to users.
- `README.md:109-126` calls the format YAML frontmatter and documents repair
  commands, but does not describe the supported subset.
- Existing parser tests live in `tests/test_metadata.py:120-169`; repair
  round-trip tests live in `tests/test_repair_metadata.py:152-185`.

Keep the current renderer and metadata field order. Do not add a third-party
YAML package or expand the public metadata schema in this plan.

## Commands you will need

| Purpose | Command | Expected on success |
|---|---|---|
| Parser tests | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_metadata tests.test_repair_metadata` | Exit 0; malformed input tests pass. |
| Full tests | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p "test_*.py"` | Exit 0. |
| Package smoke | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s project-memory/tests -p "test_*.py"` | Exit 0. |
| Syntax | `PYTHONPYCACHEPREFIX=/tmp/project-memory-pycache python3 -m py_compile project-memory/scripts/*.py` | Exit 0; no syntax errors or repository `__pycache__` changes. |

## Scope

**In scope**

- `project-memory/scripts/metadata_frontmatter.py`
- `README.md`
- `tests/test_metadata.py`
- `tests/test_repair_metadata.py`

**Out of scope**

- `metadata_validation.py` and `metadata_repair.py` semantic rules — Plan 004.
- The historical plan under `docs/superpowers/plans/` — it is not runtime input.
- Any full YAML dependency or schema redesign.

## Steps

### Step 1: Require an exact opening delimiter

Change `parse_frontmatter` so it recognizes only an opening line containing
exactly `---` with optional trailing horizontal whitespace and a newline. A
line such as `---not-frontmatter` must return `had_fm=False` and the original
text unchanged. Preserve the current handling of a leading blank line unless a
test proves it cannot be retained safely.

**Verify**: add a focused parser test and run `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_metadata` → exit 0; malformed openers are not frontmatter.

### Step 2: Reject unrecognized non-blank metadata lines

When a non-comment, non-blank line is neither a supported list item nor a
`key: value` pair, raise the existing `ValueError` path instead of silently
discarding it. This prevents repair from rewriting a file after losing text it
could not parse. Keep the existing explicit errors for flow mappings,
sequences, and nested YAML.

**Verify**: add a test that `ensure_frontmatter` raises or causes the CLI to
skip a frontmatter block containing an unrecognized top-level line, and that
the original body text remains available to the caller.

### Step 3: Document the supported subset

Update the README metadata section to say that Project Memory Metadata v1 uses
scalar `key: value` fields and indented `- item` lists only; flow mappings,
flow sequences, and nested YAML are rejected. Explain that repair skips
unsupported frontmatter rather than silently converting it.

**Verify**: `rg -n "scalar|indented|flow|nested|unsupported|frontmatter" README.md` → the supported grammar and failure behavior are present.

### Step 4: Run all checks

Run the parser, full, package smoke, and syntax commands from the Commands
table. Confirm no existing valid frontmatter test changes its body or field
order.

**Verify**: all commands exit 0 and `git diff --check` exits 0.

## Test plan

- Add a parser case for `---not-frontmatter`.
- Add an `ensure_frontmatter`/repair case proving unrecognized metadata does
  not cause silent content loss.
- Preserve existing flow/nested rejection and valid scalar/list cases.

## Done criteria

- [x] Only exact opening delimiters are accepted.
- [x] Unknown non-blank metadata lines fail closed.
- [x] README states the actual supported subset.
- [x] Existing valid metadata round-trips unchanged.
- [x] All targeted and full checks pass; Plan 003 changes stay in scope.

## STOP conditions

- A valid existing project file depends on an opening delimiter other than a
  full `---` line; stop and report the example.
- Preserving body text requires changing the renderer or metadata schema; stop
  rather than expanding this plan.
- Any test shows valid existing metadata is rewritten when no repair is needed;
  stop and investigate before proceeding.

## Maintenance notes

If the metadata schema later needs richer YAML, make that a separate migration
with compatibility fixtures. Do not silently broaden this parser in place.
