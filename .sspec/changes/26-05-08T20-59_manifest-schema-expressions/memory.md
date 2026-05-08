# Memory: manifest-schema-expressions

**Updated**: 2026-05-08T21:00:01+08:00

## Git Baseline (Immutable)

- Captured: before change file creation
- Repository: `H:/SrcCode/playground/sprout-cli`
- Branch: `main`
- HEAD: `7f45ebd35da7187f2488767763ce24e6d9c70470`
- Worktree: `clean`
- Status Snapshot: raw `git status --short --branch` output

```text
## main...origin/main [ahead 1]
```

## State

Implementation complete. Review feedback applied. Change is in REVIEW awaiting user acceptance.

## Key Files

- `.sspec/changes/26-05-08T20-59_manifest-schema-expressions/spec.md` — scope and change contract.
- `.sspec/changes/26-05-08T20-59_manifest-schema-expressions/design.md` — technical design for schema, expressions, computed variables, and conditional assets.
- `.sspec/changes/26-05-08T20-59_manifest-schema-expressions/tasks.md` — implementation progress and verification record.
- `sprout/core.py` — manifest parsing, expression evaluation, active asset source validation, conditional generation planning.
- `sprout/models.py` — manifest data model definitions.
- `sprout/cli.py` — computed evaluation in `new`, additional validation in `doctor`.
- `sprout/docs/command-authoring-guide.md` — authoring docs for schema/computed/when.

## Knowledge

- [2026-05-08T21:00:01+08:00] Decision Use `expr: "..."` for Python expressions and keep `{{...}}` for text interpolation to make executable expression fields visually distinct from template strings.
- [2026-05-08T21:00:01+08:00] Constraint User wants `template` + `content` mutual-exclusion errors to appear only when that configuration is used, not as a global blocker for unrelated commands.
- [2026-05-08T21:00:01+08:00] Decision Missing `schema` remains legacy-compatible; `schema: sprout.manifest/v1` enables the new grammar.
- [2026-05-08T21:00:01+08:00] Constraint Python expression safety is not a priority for this personal-use feature; implementation should still keep errors clear and local.
- [2026-05-08T21:00:01+08:00] Decision Missing `schema` manifests behave as current v1 for `computed` and `when`; active asset source validation applies during selected command execution and doctor checks.
- [2026-05-08T21:00:01+08:00] Decision Optional boolean inputs without defaults resolve to `False`, avoiding string/boolean comparison surprises in expressions.

## Milestones

- [2026-05-08T21:00:01+08:00] Created sspec change and drafted spec/design/tasks for manifest schema expressions.
- [2026-05-08T21:00:01+08:00] Implemented schema/computed/conditional assets and moved change to REVIEW after tests and smoke verification.
- [2026-05-08T21:00:01+08:00] Applied review feedback for missing-schema behavior and optional boolean defaults; pytest passed with 62 tests.
