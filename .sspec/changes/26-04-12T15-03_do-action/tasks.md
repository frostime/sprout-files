---
change: "do-action"
updated: ""
---

# Tasks

## Legend
`[ ]` Todo | `[x]` Done

## Tasks

### Phase 1: Manifest schema + render engine ✅
- [x] Extend manifest models and parsing for `assets[*].ref` and `actions[*]` in `sprout/models.py` and `sprout/core.py`
- [x] Upgrade template rendering in `sprout/core.py` to support `assets.<ref>.<suffix>` and `rand.*` syntax, including backward-ref validation and `/` path normalization
**Verification**: unit tests can load manifests with refs/actions; asset backward refs and random tokens render correctly; invalid refs/syntax fail with clear errors

### Phase 2: Runtime action execution + CLI surface ✅
- [x] Implement post-action planning/execution in `sprout/core.py`, and wire `sprout/cli.py` to preview/execute actions with dry-run support
- [x] Add runtime tests covering action cwd/path interpolation, dry-run non-execution, and failure propagation in `tests/`
**Verification**: `uv run python -m unittest tests.test_core tests.test_generation_policies tests.test_cli_interaction tests.test_actions`

### Phase 3: Authoring docs ✅
- [x] Update `README.md` and `sprout/templates/skill-authoring.md` to document `ref`, `actions`, path suffixes, and `rand.*`
**Verification**: docs include at least one manifest example using `ref`, `actions`, and `rand.*`, and no longer describe interpolation as identifier-only

### Feedback Tasks
- [x] Remove TOML runtime support per `revisions/001-drop-toml-support.md` in `sprout/core.py` and `pyproject.toml`
- [x] Update tests/docs/project memory to reflect YAML/YML/JSON-only support in `tests/test_core.py`, `README.md`, `.sspec/project.md`
**Verification**: `uv run python -m unittest tests.test_core tests.test_generation_policies tests.test_cli_interaction tests.test_actions`

---

## Progress

**Overall**: 100%

| Phase | Progress | Status |
|-------|----------|--------|
| Phase 1 | 2/2 | ✅ |
| Phase 2 | 2/2 | ✅ |
| Phase 3 | 1/1 | ✅ |

**Recent**:
- [x] Design approved; tasks broken down into schema/render, runtime, and docs phases
- [x] Implemented manifest ref/actions parsing, extended renderer, and post-action execution wiring
- [x] Added action tests, updated docs/examples, and validated runtime behavior in temp/runtime-action-test
- [x] Applied revision 001 to drop TOML support and re-validated runtime in temp/runtime-action-test-no-toml
