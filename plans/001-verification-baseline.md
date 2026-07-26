# Plan 001: Establish a complete verification baseline

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving on. If
> anything in the STOP conditions section occurs, stop and report. Touch only
> the files listed in Scope. Do not update `plans/README.md`; the reviewer
> maintains that index.

> **Drift check (run first)**: `git diff --stat 0766747..HEAD -- README.md tests/test_setup_project_memory.py`

## Status

- **Priority**: P1
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: tests, dx
- **Planned at**: commit `0766747`, 2026-07-14
- **Execution status**: DONE — verified in the 2026-07-27 worktree

## Why this matters

The README documents only the repo-level unittest suite, but the packaged skill
also ships `project-memory/tests/test_package_smoke.py`.
The setup tests import the module and call `main()` directly, so they do not
prove that the installed-style CLI process resolves imports and exits cleanly.
This plan makes the verification contract explicit and adds one subprocess
smoke test before higher-risk filesystem and parser changes land.

## Current state

- `README.md:95-107` documents one repo-level unittest command and a setup
  script syntax check.
- The local root `AGENTS.md` repeats the repo-level test command, but it is an
  ignored user-authored file and is not present in a clean public clone.
- `project-memory/tests/test_package_smoke.py:30-40` is a separate one-test
  suite for the packaged compatibility surface.
- `tests/test_setup_project_memory.py:24-34,48-56` loads the setup module with
  `importlib.util.spec_from_file_location` and calls `main()` in-process.
- The current verification results at the planned commit are 88 repo tests and
  one package smoke test when run as two separate commands.

Use the existing standard-library `unittest` style and temporary-directory
fixtures. Do not add a package manager, test framework, CI workflow, or a new
runtime dependency.

## Commands you will need

| Purpose | Command | Expected on success |
|---|---|---|
| Repo regression suite | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p "test_*.py"` | Exit 0; all repo tests pass (89 or more after the new test). |
| Packaged smoke suite | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s project-memory/tests -p "test_*.py"` | Exit 0; the package smoke test passes. |
| Syntax | `PYTHONPYCACHEPREFIX=/tmp/project-memory-pycache python3 -m py_compile project-memory/scripts/setup_project_memory.py` | Exit 0; no syntax errors or repository `__pycache__` changes. |

## Scope

**In scope**

- `README.md`
- `tests/test_setup_project_memory.py`

**Out of scope**

- `project-memory/tests/test_package_smoke.py` — keep the packaged smoke test
  in its existing package-local location.
- `project-memory/scripts/*.py` — this plan adds coverage only; do not change
  runtime behavior.
- `AGENTS.md` — this is an ignored local user-authored file; preserve it and do
  not attempt to package or edit it in the executor worktree.
- `.github/workflows/` — no CI workflow is part of this plan.
- Any `docs/*.md` file or installed copy under `~/.agents/skills/`.

## Steps

### Step 1: Add a standalone setup CLI smoke test

In `tests/test_setup_project_memory.py`, preserve the existing in-process
helpers and add a `subprocess.run` helper that invokes `SCRIPT_PATH` with the
current Python executable in a fresh temporary project root. Add one test that
asserts exit code 0, creates `AGENTS.md` and all four `docs/*.md` files, and
prints the existing setup summary. The test must not depend on the caller's
working directory or an existing `sys.path` mutation.

**Verify**: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_setup_project_memory` → exit 0 and the new subprocess test passes.

### Step 2: Document both shipped test suites

Update the `Validate` section of `README.md` to show the repo regression command
and the package smoke command. Keep the documented syntax check and the
no-package-manager statement. Make it clear that both unittest commands are
required for a complete check. Do not edit the ignored local `AGENTS.md`.

**Verify**: `rg -n "project-memory/tests|PYTHONDONTWRITEBYTECODE|unittest discover" README.md` → the public README contains both test roots and the cache-safe commands.

### Step 3: Run the complete baseline

Run both unittest commands and the syntax command from the repository root.
Do not claim a single total that hides the two suites; report each count.

**Verify**: the three commands in the Commands table all exit 0; expected
result is 89 repo tests plus 1 package smoke test, with no `__pycache__` changes.

## Test plan

- Add one subprocess regression in `tests/test_setup_project_memory.py`.
- Cover executable import resolution, exit code, summary output, and created
  files. Keep existing in-process behavior tests unchanged.
- Run the existing repo suite and the package-local smoke suite separately.

## Done criteria

- [x] The setup CLI is exercised in a subprocess from a fresh temporary root.
- [x] README documents both unittest roots.
- [x] Both unittest commands and `py_compile` pass.
- [x] Plan 001 implementation changes are limited to the two in-scope files.

## STOP conditions

- The setup script cannot be invoked as a standalone subprocess from a clean
  temporary root; stop and report the exact import or exit error.
- The package-local test cannot be discovered with the documented command; do
  not move or duplicate it without reporting first.
- The public README is absent or its layout differs materially from the
  Current state excerpt; stop and report rather than editing a local AGENTS.md.
- The change appears to require a package manager, CI workflow, or runtime
  code change; stop instead of expanding scope.

## Maintenance notes

When a new shipped test root or executable script is added, update the public
README verification section. Keep local ignored `AGENTS.md` guidance in the
user's project and do not treat it as part of the public package.
