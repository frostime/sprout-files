---
name: manifest-schema-expressions
status: REVIEW
change-type: single
created: 2026-05-08T20:59:53
reference: null
---

# manifest-schema-expressions

## Problem Statement

Current `manifest.yaml` has no explicit schema/version marker and only supports direct input variables, causing feature evolution (`computed`, conditional assets, stricter asset validation) to rely on implicit structure and making expression semantics ambiguous for users and future maintainers.

## Proposed Solution

### Approach

Add a small v1 manifest schema layer with explicit expression-bearing fields. Keep existing manifests compatible by treating missing `schema` as legacy/current behavior, while `schema: sprout.manifest/v1` enables the new grammar.

Use two visibly different syntaxes: `{{...}}` remains text interpolation for paths/templates/content, while `expr: "..."` is Python-expression evaluation for `computed` and conditional asset `when`. This keeps string rendering and executable expressions easy to distinguish in YAML and in implementation.

Validation is command-scoped: invalid asset `template`/`content` combinations should fail when the command is checked by `doctor` or executed by `sprout new <command>`, without preventing unrelated commands from being listed or used.

### Key Change

**Feat A: Manifest Schema Field**
- Add optional manifest `schema` field.
- Support `schema: sprout.manifest/v1`.
- Missing `schema` remains legacy-compatible.
- Unknown/future schema produces a command-level validation error.

**Fix B: Active Asset Content Source Validation**
- For active `file` assets, require exactly one of `template` or `content`.
- For active `dir` assets, reject `template` and `content`.
- Apply this as command-level validation during `doctor` and `sprout new <command>`.
- Conditional assets with `when.expr == false` are skipped before this asset content-source validation.

**Feat C: Computed Variables**
- Add `computed` after `inputs` and before `assets`.
- Each computed entry defines `name` + `expr`.
- Evaluate in declaration order after input collection and built-in context creation, before asset planning.
- Inject computed values into the normal template context so assets and actions can use `{{computed_name}}`.

**Feat D: Conditional Assets**
- Add optional `when.expr` to assets.
- If the expression is truthy, the asset participates in planning/generation.
- If falsy, the asset is skipped: no path rendering, no content validation, no ref registration.
- Later references to skipped asset refs fail as existing unknown asset reference errors.

**Docs E: Authoring Documentation**
- Update built-in command authoring docs with schema, computed, conditional assets, and expression/interpolation distinction.
- Add examples that show `{{...}}` for text and `expr` for Python expressions.

**Tests F: Runtime Coverage**
- Cover schema acceptance/rejection, lazy command-scoped validation, computed variable rendering, conditional asset skip/include behavior, and asset content-source errors.

### Scope Summary

| File | Change |
|---|---|
| `sprout/models.py` | Add manifest schema, computed spec, and conditional asset data model fields. |
| `sprout/core.py` | Parse schema/computed/when, evaluate expressions, validate active asset sources, integrate computed/conditions into generation planning. |
| `sprout/cli.py` | Ensure `new` validates only the selected command while `doctor` reports all command issues. Minimal output changes only where errors become clearer. |
| `sprout/docs/command-authoring-guide.md` | Document new schema and expression fields. |
| `sprout/templates/builtin-command-manifest.yaml` | Add concise commented examples for schema/computed/when if not too noisy. |
| `tests/` | Add/update tests for the new manifest behavior. |

What stays unchanged:
- `{{...}}` interpolation remains simple text replacement.
- Existing manifests without `schema` continue to work.
- No Jinja-style control flow is added.
- Global/project discovery rules stay unchanged.

### Design Reference

→ See [design.md](./design.md)
