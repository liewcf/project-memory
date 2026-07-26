# Plan 004: Validate metadata semantics

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving on. If
> anything in the STOP conditions section occurs, stop and report. Touch only
> the files listed in Scope. Do not update `plans/README.md`; the reviewer
> maintains that index.

> **Drift check (run first)**: `git diff --stat 0766747..HEAD -- project-memory/scripts/metadata_defaults.py project-memory/scripts/metadata_validation.py project-memory/scripts/metadata_repair.py tests/test_metadata.py tests/test_validate_metadata.py`

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: LOW
- **Depends on**: `plans/001-verification-baseline.md`
- **Category**: correctness
- **Planned at**: commit `0766747`, 2026-07-14
- **Execution status**: DONE — verified in the 2026-07-27 worktree

## Why this matters

Validation currently checks only the shape `YYYY-MM-DD`, so impossible dates
such as `2026-02-31` pass. The validator accepts any allowed `doc_type` even
when it conflicts with the filename, although the defaults define one type per
memory file. Repair has the same filename-insensitive behavior. Tightening both
rules makes `validate_metadata.py` a trustworthy check without changing the
four-file model.

## Current state

- `project-memory/scripts/metadata_validation.py:16` defines a shape-only
  regular expression; `_validate_dates` uses it at lines 58-64.
- `metadata_validation.validate_metadata(data, filename)` accepts a filename
  at `:19-21` but does not use it.
- `project-memory/scripts/metadata_defaults.py:58-109` defines the expected
  `doc_type` for each known filename.
- `project-memory/scripts/metadata_repair.py:38-53` repairs only missing or
  globally invalid `doc_type` values, not a valid-but-wrong type for a known
  filename.
- Existing tests cover wrong formats and globally invalid types at
  `tests/test_metadata.py:222-244` and `tests/test_validate_metadata.py:113-138`.

Keep the public CLI output style, standard-library-only implementation, and
generic metadata vocabulary. Unknown filenames passed directly to the helper
must remain supported without inventing a new mapping.

## Commands you will need

| Purpose | Command | Expected on success |
|---|---|---|
| Targeted tests | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_metadata tests.test_validate_metadata tests.test_repair_metadata` | Exit 0; new semantic cases pass. |
| Full tests | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p "test_*.py"` | Exit 0. |
| Package smoke | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s project-memory/tests -p "test_*.py"` | Exit 0. |
| Syntax | `PYTHONPYCACHEPREFIX=/tmp/project-memory-pycache python3 -m py_compile project-memory/scripts/*.py` | Exit 0; no syntax errors or repository `__pycache__` changes. |

## Scope

**In scope**

- `project-memory/scripts/metadata_defaults.py` (only if a small expected-type
  constant is cleaner than rebuilding defaults)
- `project-memory/scripts/metadata_validation.py`
- `project-memory/scripts/metadata_repair.py`
- `tests/test_metadata.py`
- `tests/test_validate_metadata.py`
- `tests/test_repair_metadata.py`

**Out of scope**

- Frontmatter parsing grammar — Plan 003.
- New metadata fields, new filenames, or a new schema version.
- CLI output redesign or third-party date/YAML packages.

## Steps

### Step 1: Validate real calendar dates

Replace or augment the shape-only check with `datetime.date.fromisoformat`
after ensuring the value is a string in the documented ISO format. Return the
existing `Invalid date format for <field>` style error for both malformed and
impossible dates. Use the same rule in repair when deciding whether a date is
invalid; do not change valid historical dates solely because they are old.

**Verify**: add tests for `2026-02-31` and a valid leap-day date, then run the
targeted test command → exit 0.

### Step 2: Enforce the filename-to-type mapping

When `filename` is one of the four known memory files, compare `data["doc_type"]`
with the expected type from the existing defaults. Add a clear validation error
for a valid-but-wrong type. In repair, replace a mismatched type with the
known file’s default while preserving the existing `updated`-date behavior.
When `filename` is omitted or unknown, retain the current allowed-values-only
validation.

**Verify**: add validation and repair tests for `TASKS.md` carrying
`doc_type: context`, then run the targeted test command → exit 0 and the type
is corrected or rejected as specified.

### Step 3: Run all checks

Run the full, package-local, and syntax checks. Confirm existing tests for
globally invalid types and historical dates still pass.

**Verify**: all commands exit 0 and `git diff --check` exits 0.

## Test plan

- Validator: impossible date, valid leap day, known filename with wrong allowed
  type, unknown filename with allowed type.
- Repair: impossible date is replaced, known-file type is corrected, valid old
  date is preserved without `--touch`.
- Follow the existing direct-helper tests in `tests/test_metadata.py` and CLI
  tests in `tests/test_validate_metadata.py`.

## Done criteria

- [x] Impossible calendar dates fail validation and are repaired.
- [x] Known filenames enforce their expected `doc_type`.
- [x] Unknown/direct helper filenames retain generic allowed-value behavior.
- [x] Existing test suites and compile checks pass.
- [x] Plan 004 implementation changes are limited to the in-scope files.

## STOP conditions

- Existing callers rely on `filename` to mean something other than one of the
  four memory files; stop and report the caller before changing semantics.
- Date values are stored with a documented non-ISO format; stop and update the
  plan rather than silently rejecting them.
- The fix requires changing frontmatter parsing; leave that to Plan 003.

## Maintenance notes

Any future memory filename must add its expected type and tests in the same
change. Keep the validator and repair rules driven by one shared source of
truth so they cannot drift again.
