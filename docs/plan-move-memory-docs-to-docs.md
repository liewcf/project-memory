# Move Project Memory Docs Under `docs/`

## Summary

Move the project-memory convention from root-level memory docs to `docs/`, while keeping `AGENTS.md` at the repository root. The setup workflow should create or migrate:

```text
AGENTS.md
docs/PROJECT_CONTEXT.md
docs/DECISIONS.md
docs/TASKS.md
docs/CHANGELOG_WORK.md
```

This repo's existing ignored memory files should be moved into `docs/`, and `.gitignore` should keep them private under the new paths.

## Key Changes

- Update the skill instructions and README to describe `docs/` as the location for project memory docs, with root `AGENTS.md` as the pointer file future agents read first.
- Update `setup_project_memory.py` so new setup creates `docs/` and the four memory docs inside it.
- Add migration behavior: if legacy root memory files exist and the matching `docs/` file does not, move the existing file into `docs/` rather than creating a fresh placeholder.
- Preserve idempotency: rerunning setup should not duplicate `AGENTS.md` guidance, overwrite existing docs, or recreate legacy root memory files.
- Update the `AGENTS.md` requirement text to reference `docs/PROJECT_CONTEXT.md`, `docs/DECISIONS.md`, `docs/TASKS.md`, and `docs/CHANGELOG_WORK.md`.

## Existing Repo Update

- Move this repo's current ignored files into `docs/`:
  - `PROJECT_CONTEXT.md` -> `docs/PROJECT_CONTEXT.md`
  - `DECISIONS.md` -> `docs/DECISIONS.md`
  - `TASKS.md` -> `docs/TASKS.md`
  - `CHANGELOG_WORK.md` -> `docs/CHANGELOG_WORK.md`
- Keep root `AGENTS.md`, but update its repository layout and project memory requirement to point to `docs/`.
- Update `.gitignore` from root-only ignores to ignore both current local memory paths:
  - `AGENTS.md`
  - `docs/PROJECT_CONTEXT.md`
  - `docs/DECISIONS.md`
  - `docs/TASKS.md`
  - `docs/CHANGELOG_WORK.md`
- Do not ignore all of `docs/`, so future public documentation can still be tracked.

## Tests

- Update the setup creation test to expect `AGENTS.md` at root and the four memory docs under `docs/`.
- Add or update an idempotency test to confirm a second setup run makes no duplicate `AGENTS.md` requirement and no legacy root docs.
- Add a migration test where legacy root memory files already exist; setup should move/preserve their content under `docs/`.
- Keep the existing test for preserving user-authored `AGENTS.md` content.
- Verify with:
  - `python3 -m unittest discover -s tests -p "test_*.py"`
  - `python3 -m py_compile project-memory/scripts/setup_project_memory.py`

## Assumptions

- `docs/` means a repository-root `docs/` directory, not an absolute filesystem `/docs`.
- Root `AGENTS.md` remains the only root-level project memory file.
- The migration should preserve existing memory content exactly except for path references that intentionally need updating.
- The installed profile copy at `~/.agents/skills/project-memory/` should be synced only after the repo change is implemented and verified.
