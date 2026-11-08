# Project Memory State Transitions

These tables describe the existing code and workflow contracts. They do not
start actions, grant authorization or introduce a project-management system.

## Implementation States

| Owner | State or transition | Guard and failure behavior |
|---|---|---|
| Setup orchestration | Preflight → migration → missing docs → AGENTS requirement → summary | Preflight checks known paths and legacy syntax before writes. Later failures stop setup; completed file operations remain. Rerun against the current files. |
| `MemoryLocation.ABSENT` | Neither root nor docs copy exists → create docs template | Creation must not overwrite a destination that appears meanwhile. |
| `MemoryLocation.LEGACY_ONLY` | Root copy → parsed content → staged docs copy → published docs copy → source removed | Parse before publication; remove the source only after publication and a source-version check. A removal failure leaves both copies. |
| `MemoryLocation.DOCS_ONLY` | Docs copy exists → preserve it | Setup does not validate or repair existing docs metadata. |
| `MemoryLocation.CONFLICT` | Both copies exist → preserve both and report root file left in place | Do not merge or delete either automatically. |
| AGENTS requirement | Missing file → create; missing section → append; stale section → refresh; current section → unchanged | Refresh checks required phrases and refuses detected changes since its read. Use the setup preflight in `modes.md` to preserve custom section content before running the script. |
| Frontmatter envelope | No opening delimiter → absent; opening and closing delimiters → parse; opening without closing delimiter → error | Malformed frontmatter must not be treated as ordinary body content and wrapped in a new header. |
| `_FieldState.NO_KEY` | Key/value → `EMPTY` or `SCALAR` | An indented list item without a key is invalid. Mapping colons require whitespace or end-of-line before entering a field state. |
| `_FieldState.EMPTY` | First list item → `LIST`; next key → `EMPTY` or `SCALAR` | A bare key remains `None` until it receives a list item. |
| `_FieldState.SCALAR` | Next key → `EMPTY` or `SCALAR` | A list item cannot overwrite a scalar. |
| `_FieldState.LIST` | Same-indentation item → append; next key → `EMPTY` or `SCALAR` | Changed indentation is unsupported nesting. Comments and blank lines preserve the current state. Duplicate keys are invalid in every state. |
| Scalar syntax | Opening quote → quoted string; otherwise plain scalar → optional inline comment | Fields and list items share syntax checks. Quoted constructs remain literal strings; unquoted collections, mappings, anchors, aliases, tags and block scalars are rejected. A comment-only field is `EMPTY`; a comment-only list item is unsupported. |
| Metadata repair | Unchanged → changed when any field needs repair | `changed` is monotonic during one call. Preserve valid values; repair invalid defaults. Refresh `updated` for any repair, or for explicit `--touch` when its date differs from today. |
| Frontmatter result | Absent → `added`; existing with changes → `updated`; existing without changes → `unchanged` | Return original text exactly for `unchanged`. Before returning changed text, reparse generated metadata and check it matches the intended values; a mismatch produces no replacement text. |
| Repair command | Read → create missing / skip unchanged / publish repaired / skip error / report published cleanup warning | A handled error or cleanup warning sets `had_error` permanently for this run. Continue other files and exit 1 if any occurred. `PUBLISHED` means the file was saved despite the nonzero exit. |
| Validation | Read → parse → required fields → semantic checks → pass/fail | Missing required fields stop deeper metadata checks. `any_fail` is monotonic across files and determines the exit code. Validation does not write. |
| File access | Required primitives → safe directory descriptor → no-follow file open → regular-file check → read or stage → close | Unsupported runtime primitives and unsafe paths fail closed. |
| Versioned read | Capture file version → read text → verify same descriptor version → return text and version | Reject edits detected during the read. Repair and AGENTS refresh carry that version into replacement; reads do not count access-time changes as edits. |
| File publication | Verify expected read-time version → stage → preserve metadata → flush/sync → publish → remove temporary name | Creation uses an exclusive hard link; replacement uses atomic rename. Preserve ownership, permission bits, ACLs and extended attributes before publication; fail if preservation is unavailable. Reject a supplied read-time version mismatch before staging and detected changes during staging before replacement. Failed staging/publication leaves the destination intact. |
| `_PublicationState` | `STAGED` → `PUBLISHED_WITH_TEMP` after link, or `PUBLISHED` after rename | Rename consumes the temporary name. For a linked destination, cleanup failure raises `PublishedCleanupError` with the saved destination and retained temporary name. This is distinct from a failed publication. |

Publication replaces a directory entry, not the old inode. Hard-linked aliases
keep their old contents. Metadata preservation uses Darwin's descriptor-based
ACL get/set APIs and `fcopyfile` for xattrs, or Linux's descriptor-based xattr
APIs. Darwin replaces ACLs exactly, including clearing inherited entries when
the source has no ACL; other runtimes fail closed
when copying an existing file. A process crash may leave a temporary file or two migration
copies; setup does not automatically remove such recovery material. No command
provides a transaction across all files, interprocess locking or a full
power-loss durability guarantee.

If publication succeeds but temporary-file cleanup fails, setup stops with an
explicit publication warning and a nonzero exit; migration leaves its legacy
source in place. Repair reports `PUBLISHED` with a warning, continues other
files and exits nonzero. Inspect the saved destination and retained temporary
name rather than assuming the file was skipped.

## Workflow States

| Subject | Transition | Required guard |
|---|---|---|
| Context readiness | Root identified → memory read → current evidence checked → ready to act | Recheck transient prerequisites before resuming saved work. |
| Memory maturity | Missing → templates with unknown facts → evidence-populated → reconciled when stale | Setup creates structure; update records verified facts. Creating metadata does not verify its body. |
| Completion memory check | Task finished → assess durable change → skip or update | Update only when durable context changed and writing is authorized. |
| Maintenance | Defects found → recommend repair; excessive noise → recommend compact | Review/status stay read-only by default. Compaction requires a request. |
| Result evidence | Unverified → scoped observation → current evidence; contradicted → reconciled or historical | Match the target and observation date. Evidence for another artifact does not supersede this one. |
| Work and authorization | Proposed / completed; checks pending / passed; limitations open / accepted; action unauthorized / authorized | These are independent dimensions. Completion is not verification, and acceptance is not permission to execute. |
| Operating guidance | Observation → current recurring rule → AGENTS edit → readback verified | Keep temporary task state and history in docs; preserve user-authored guidance. |
| Skill installation | Source changed → validated → installed copy synced → available in a session | Verify each boundary separately; a sync does not prove a running session reloaded. |
| Plan status | TODO / IN PROGRESS / BLOCKED / REJECTED / DONE | Respect dependencies; use DONE only with implementation and verification evidence for the checkout. |

Metadata `status` values (`active`, `stable`, `archived`, `draft`) are document
labels. Validation checks membership; it does not enforce transitions between
them or certify completion, factual accuracy, verification or authorization.
