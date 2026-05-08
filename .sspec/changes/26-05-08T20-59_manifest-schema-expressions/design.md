---
change: "manifest-schema-expressions"
created: 2026-05-08T20:59:53
---

# Design: manifest-schema-expressions

## Target Manifest Shape

```yaml
schema: sprout.manifest/v1

name: issue
description: Create an issue document

inputs:
  - name: name
    type: string
    description: Issue title

  - name: with_tests
    type: boolean
    default: false

computed:
  - name: slug
    expr: "name.strip().lower().replace(' ', '-')"

  - name: issue_id
    expr: "f'{YY}{MM}{DD}-{slug}'"

assets:
  - type: dir
    path: "issues/{{slug}}"
    ref: issue_dir

  - type: file
    path: "{{assets.issue_dir.rel_path}}/issue.md"
    template: issue.md

  - type: file
    when:
      expr: "with_tests"
    path: "{{assets.issue_dir.rel_path}}/test.md"
    content: |
      # Test Plan for {{name}}
```

## Syntax Boundary

| Syntax | Meaning | Allowed location |
|---|---|---|
| `{{name}}` | Text interpolation | String fields such as `path`, `content`, template files, action strings |
| `expr: "..."` | Python expression evaluation | `computed[*].expr`, `assets[*].when.expr` |

## Data Model Additions

```python
ManifestSchema = Literal['legacy', 'sprout.manifest/v1']

@dataclass(slots=True)
class ComputedSpec:
    name: str
    expr: str

@dataclass(slots=True)
class ConditionSpec:
    expr: str

@dataclass(slots=True)
class AssetSpec:
    type: AssetType
    path: str
    template: str | None = None
    content: str | None = None
    ref: str | None = None
    when: ConditionSpec | None = None

@dataclass(slots=True)
class CommandSpec:
    name: str
    description: str
    package_dir: Path
    manifest_path: Path
    inputs: list[InputSpec]
    computed: list[ComputedSpec]
    assets: list[AssetSpec]
    actions: list[ActionSpec]
    conflict: ConflictPolicy | None = None
    root: str | None = None
    schema: str | None = None
```

## Runtime Flow

```text
sprout new <command>
  → load selected CommandSpec
  → collect_inputs()
  → build_variable_context()
  → render_input_values()
  → evaluate_computed_values()
  → build_generation_plan()
      for each asset:
        → evaluate when.expr if present
        → if false: skip before path/content validation
        → validate active asset source rules
        → render path/template/content
        → register ref only if active
  → apply_generation_plan()
  → plan_post_actions()
```

## Expression Evaluation Contract

```python
def evaluate_expression(expr: str, context: dict[str, Any], *, label: str) -> Any: ...

def evaluate_computed_values(command: CommandSpec, context: dict[str, Any]) -> None: ...

def is_asset_active(asset: AssetSpec, context: dict[str, Any], *, label: str) -> bool: ...
```

Initial expression environment:

| Name source | Availability |
|---|---|
| Inputs | `computed` and `when.expr` |
| Built-in time variables | `computed` and `when.expr` |
| Prior computed values | Later `computed`, all `when.expr` |
| Asset refs | Not available in `computed`; available to later asset `when.expr` only if previous active assets registered refs |

Implementation boundary:
- Use direct Python `eval()` with a small explicit globals dict.
- Convert expression exceptions into `ValidationError` with command/field context.
- Avoid adding a custom expression language in this change.

## Validation Timing

| Operation | Behavior |
|---|---|
| `sprout list` | Loads registry; should not fail unrelated commands because of active asset source problems. |
| `sprout list --all` | May show manifest parse/schema errors already collected during load. |
| `sprout doctor` | Reports schema, computed, expression, template variable, and active asset source issues across all commands. |
| `sprout new <command>` | Fails only if the selected command has errors encountered during its own execution/validation. |
| `sprout new other-command` | Not affected by a different invalid command. |

## Active Asset Source Rules

| Asset state | Rule |
|---|---|
| `type: file`, active | exactly one of `template` or `content` |
| `type: dir`, active | neither `template` nor `content` |
| `when.expr` false | skip path rendering, source validation, creation, and ref registration |

## Compatibility Strategy

| Manifest | Behavior |
|---|---|
| Missing `schema` | Legacy-compatible; existing manifests continue to run. |
| `schema: sprout.manifest/v1` | Enables `computed` and `when.expr`; uses v1 validations. |
| Unknown schema | Command-level validation error. |

No file migration is planned in this change.
