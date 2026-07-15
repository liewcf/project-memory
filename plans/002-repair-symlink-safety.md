# Plan 002: Reject symlinked repair targets

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving on. If
> anything in the STOP conditions section occurs, stop and report. Touch only
> the files listed in Scope. Do not update `plans/README.md`; the reviewer
> maintains that index.

> **Drift check (run first)**: `git diff --stat 0766747..HEAD -- project-memory/scripts/setup_project_memory.py project-memory/scripts/repair_metadata.py tests/test_setup_project_memory.py tests/test_repair_metadata.py`

## Status

- **Priority**: P1
- **Effort**: M
- **Risk**: MED
- **Depends on**: `plans/001-verification-baseline.md`
- **Category**: security
- **Planned at**: commit `0766747`, 2026-07-14

## Why this matters

`repair_metadata.py --root PATH` writes to `PATH/docs/*.md` without rejecting
symlinked directories or files. A symlink inside the selected project can make
the repair command overwrite a target outside that project. The setup script
already has a safe-path helper, so the fix should share that boundary and add
regression tests for both existing and dangling symlinks.

## Current state

- `project-memory/scripts/repair_metadata.py:42-67` creates `docs/` and missing
  files directly from `root / DOCS_DIR`.
- `project-memory/scripts/repair_metadata.py:70-94` reads and writes existing
  memory files directly, with no `is_symlink()` or resolved-root check.
- `project-memory/scripts/setup_project_memory.py:160-174` defines
  `ensure_safe_project_path`, which rejects symlinked candidates and paths that
  resolve outside the project root.
- Existing setup tests cover symlinked `AGENTS.md`, `docs/`, and a broken docs
  file at `tests/test_setup_project_memory.py:263-295`; repair has no equivalent
  tests in `tests/test_repair_metadata.py`.

Preserve the current four-file model, standard-library-only runtime, and
user-facing repair output. A legitimate project must not be able to opt out of
the boundary by passing a different relative path.

## Commands you will need

| Purpose | Command | Expected on success |
|---|---|---|
| Targeted tests | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_setup_project_memory tests.test_repair_metadata` | Exit 0; all targeted tests pass. |
| Full tests | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p "test_*.py"` | Exit 0. |
| Package smoke | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s project-memory/tests -p "test_*.py"` | Exit 0. |
| Syntax | `PYTHONPYCACHEPREFIX=/tmp/project-memory-pycache python3 -m py_compile project-memory/scripts/*.py` | Exit 0; no syntax errors or repository `__pycache__` changes. |

## Scope

**In scope**

- `project-memory/scripts/setup_project_memory.py`
- `project-memory/scripts/repair_metadata.py`
- `project-memory/scripts/path_safety.py` (create only if a shared helper is needed)
- `tests/test_setup_project_memory.py`
- `tests/test_repair_metadata.py`

**Out of scope**

- `project-memory/scripts/validate_metadata.py` — read-only validation does not
  write outside the root.
- Any change to the four-file memory model, CLI flags, or installed profile copy.
- Atomic-write changes; that is a separate follow-up.

## Steps

### Step 1: Share the existing safe-path boundary

Move the existing `ensure_safe_project_path` implementation into a small
standard-library helper module if that is the smallest way to import it from
both scripts. Update setup imports without changing its current behavior. In
repair, retain the resolved-root check, then open the `docs/` directory and each
memory file through descriptor-relative operations with `O_NOFOLLOW` (and
`O_DIRECTORY` for `docs/`) before every read, create, truncate, or write. Do not
make safety depend on a pre-check followed by `Path.write_text`; reject a
symlink at the operating-system open point.

Before choosing those primitives, establish which operating systems the
repository currently supports and verify the required no-follow behavior on
each of them. Do not add an unconditional `O_NOFOLLOW` import or make all normal
repairs fail on a platform where it is unavailable. If the standard library
cannot provide equivalent race-safe semantics on a supported platform, stop and
request an explicit portability decision before changing runtime behavior; do
not ship an unsafe fallback or silently narrow platform support.

**Verify**: `PYTHONPYCACHEPREFIX=/tmp/project-memory-pycache python3 -m py_compile project-memory/scripts/*.py` → exit 0 with no repository `__pycache__` changes.

### Step 2: Handle rejected paths as a clean CLI failure

Catch the safe-path rejection in `repair_metadata.py`, print a concise
`SKIPPED` or `ERROR` message naming only the relative memory path, and return
exit code 1. Do not print target contents or attempt a fallback write.

**Verify**: run the repair CLI against a temporary root with a symlinked
`docs/` directory and against a dangling symlink at `docs/TASKS.md` → exit 1,
outside targets remain unchanged, and no traceback is required for the user.

### Step 3: Add regression tests

Extend the existing temporary-root tests to cover: symlinked `docs/`, an
existing symlinked memory file, and a dangling symlinked memory file. Assert
that the command fails, the outside target is not created or modified, and
normal non-symlink roots still repair successfully. Cover the descriptor-level
no-follow helper directly if a deterministic symlink-swap test is impractical,
and add platform-appropriate coverage for every supported implementation path.

**Verify**: the targeted test command passes and includes the new cases.

## Test plan

Use `RepairMetadataRootTests` in `tests/test_repair_metadata.py` as the fixture
pattern and the setup symlink tests as the expected assertion style. Tests must
use temporary directories and must not create symlinks inside the repository.

## Done criteria

- [ ] Setup and repair share one safe resolved-root/symlink boundary.
- [ ] Repair rejects symlinked directories, existing files, and dangling files.
- [ ] Every repair target is opened with no-follow semantics, so a symlink at
  the open point is rejected before it can be read or modified.
- [ ] Supported-platform behavior is established from repository evidence, and
  every supported platform retains normal non-symlink repair behavior.
- [ ] No platform is silently dropped or made unusable because a POSIX-only
  constant or descriptor flag is unavailable.
- [ ] Targeted, full, package smoke, and compile checks pass.
- [ ] Only the in-scope files are changed.

## STOP conditions

- The helper cannot be imported when `repair_metadata.py` is invoked directly;
  stop and report instead of changing the installation layout.
- A supported platform lacks standard-library primitives that can enforce the
  same race-safe no-follow boundary; stop and request a portability decision
  instead of shipping a platform-wide failure or an unsafe fallback.
- A normal non-symlink project currently relies on a path that resolves outside
  its root; stop and report the example rather than adding an exception.
- The fix requires changing validation or metadata semantics; leave that to
  Plan 004.

## Maintenance notes

Any future script that writes project memory must use the same resolved-root and
descriptor-level no-follow boundary before opening a path. Review new `--root`
or migration features specifically for dangling symlinks, parent-directory
symlinks, and file-descriptor lifetime.
