---
change: "builtin-command-bootstrap"
updated: ""
---

# Tasks

## Legend
`[ ]` Todo | `[x]` Done

## Tasks

### Phase 1: CLI + authoring directory foundation ✅
- [x] Add `builtin` command and `buildin` alias in `sprout/cli.py`, wiring to new scaffold execution flow.
- [x] Add authoring directory helpers and dual-directory registry discovery in `sprout/core.py` per spec Feat B / Compat C.
- [x] Add builtin manifest generation and legacy-directory migration helpers in `sprout/scaffold.py`.
**Verification**: `uv run python -m unittest tests.test_core tests.test_cli_interaction` covers new command dispatch, directory resolution, and compatibility behavior.

### Phase 2: Docs, templates, and init scaffold ✅
- [x] Add builtin manifest template under `sprout/templates/` and update init/profile/example strings to prefer `__new__/` paths.
- [x] Update `README.md`, `sprout/docs/user-guide.md`, and `sprout/docs/command-authoring-guide.md` to document `sprout builtin <name>` and `commands` compatibility.
- [x] Update `tests/test_init.py` for new default directory and scaffold expectations.
**Verification**: `uv run python -m unittest tests.test_init` and doc text references consistently use `.sprout/__new__/` as the preferred authoring path.

### Phase 3: End-to-end regression and cleanup ✅
- [x] Add/adjust compatibility tests in `tests/test_core.py` and `tests/test_cli_interaction.py` for migration, merge, and conflict handling.
- [x] Run targeted unittest suite and one runtime smoke test in `temp/<runtime-test-dir>` using `uv run sprout`.
- [x] Update change memory/progress records after verification.
**Verification**: `uv run python -m unittest` passes for touched areas, and smoke test confirms `sprout builtin demo` creates `.sprout/__new__/demo/manifest.yaml`.

---

## Progress

**Overall**: 100%

| Phase | Progress | Status |
|-------|----------|--------|
| Phase 1 | 100% | ✅ |
| Phase 2 | 100% | ✅ |
| Phase 3 | 100% | ✅ |

**Recent**:
- [2026-04-12T17:29:00+08:00] User approved design gate; tasks planned and implementation started.
- [2026-04-12T17:43:31+08:00] 完成 builtin/buildin、`__new__/commands` 兼容、文档更新、测试与 runtime smoke test。
