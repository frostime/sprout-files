---
change: "manifest-schema-expressions"
updated: "2026-05-08T21:00:01+08:00"
---

# Tasks

## Legend
`[ ]` Todo | `[x]` Done

## Tasks

### Feedback Tasks ✅
- [x] Treat missing `schema` manifests as current v1 behavior for `computed` and `when` instead of gating those fields.
- [x] Make optional boolean inputs without defaults resolve to `False` instead of `''`.
- [x] Add tests for missing-schema v1 fields and boolean coercion/default behavior.
**Verification**: `uv run pytest` passed with 62 tests.

### Phase 1: Schema + Data Model ✅
- [x] Update `sprout/models.py` with `ComputedSpec`, `ConditionSpec`, and new `CommandSpec`/`AssetSpec` fields per design.
- [x] Update `sprout/core.py` manifest parsing for `schema`, `computed`, and `when`.
- [x] Add parse-time validation for unknown schema and malformed `computed`/`when` shapes.
**Verification**: `uv run pytest` passed.

### Phase 2: Expression Runtime ✅
- [x] Add expression evaluator helpers in `sprout/core.py` per design.
- [x] Evaluate `computed` after input context creation and before generation planning.
- [x] Ensure computed variable name collisions and expression failures produce `ValidationError` with field context.
**Verification**: `uv run pytest` passed; smoke test rendered computed `slug` into asset paths.

### Phase 3: Conditional Assets + Active Source Validation ✅
- [x] Update `build_generation_plan()` in `sprout/core.py` to evaluate `assets[*].when.expr` before rendering the asset.
- [x] Add active asset source validation for `file` and `dir` assets.
- [x] Ensure skipped assets do not register refs and later active references fail through existing missing-reference behavior.
**Verification**: `uv run pytest` passed; smoke test covered conditional include/skip behavior.

### Phase 4: CLI Integration + Doctor Behavior ✅
- [x] Ensure `sprout new <command>` validates/evaluates only the selected command path.
- [x] Extend `doctor` path to report new validation/expression issues across all valid commands.
- [x] Keep `list` behavior tolerant of unrelated command-level runtime validation issues.
**Verification**: CLI tests cover one invalid command not blocking another command, while `doctor` reports the issue.

### Phase 5: Docs + Templates ✅
- [x] Update `sprout/docs/command-authoring-guide.md` with schema, computed, `when.expr`, and syntax boundary examples.
- [x] Update `sprout/templates/builtin-command-manifest.yaml` only if a concise comment improves discoverability without making the starter noisy.
- [x] Update README only if CLI-visible behavior changes need top-level mention.
**Verification**: docs examples match implemented syntax; no README update needed.

### Phase 6: Full Verification ✅
- [x] Run `uv run pytest`.
- [x] Run manual smoke tests in `temp/<runtime-test-dir>` using `uv run sprout` for computed + conditional asset manifests.
- [x] Run `uv run sprout doctor` in the project root if `.sprout/` fixtures remain valid.
**Verification**: all tests passed; smoke output matched expected created/skipped assets.

---

## Progress

**Overall**: 100%

| Phase | Progress | Status |
|-------|----------|--------|
| Feedback | 3/3 | ✅ |
| Phase 1 | 3/3 | ✅ |
| Phase 2 | 3/3 | ✅ |
| Phase 3 | 3/3 | ✅ |
| Phase 4 | 3/3 | ✅ |
| Phase 5 | 3/3 | ✅ |
| Phase 6 | 3/3 | ✅ |

**Recent**:
- 2026-05-08T21:00:01+08:00 Drafted implementation plan for schema, computed expressions, and conditional assets.
- 2026-05-08T21:00:01+08:00 Implemented schema/computed/conditional asset support, updated docs/tests, and verified with pytest + smoke test.
- 2026-05-08T21:00:01+08:00 Applied review feedback: missing schema now behaves as current v1, optional booleans default to False, and pytest passes with 62 tests.
