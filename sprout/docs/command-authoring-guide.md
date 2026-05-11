# Sprout Command Authoring Guide

How to create and maintain `.sprout/__new__/<name>/` command packages.

---

## Annotated Example

A complete manifest showing all features. Use as a copy-paste starting point:

```yaml
# .sprout/__new__/issue/manifest.yaml
schema: sprout.manifest/v1

name: issue
description: Create an issue document

# Per-command conflict policy. If omitted, falls back to
# .sprout/config.yaml → 'fail' (hard-coded default).
conflict: fail

inputs:
  - name: name
    type: string
    required: true
    description: Issue title

  - name: type
    type: enum
    enum: [bug, feat, refactor]
    default: bug

  - name: with_tests
    type: boolean
    default: false

computed:
  - name: slug
    expr: "name.strip().lower().replace(' ', '-')"

assets:
  # dirs before files — sprout sorts automatically, but declare in order for clarity
  - type: dir
    path: issues/{{slug}}
    ref: issues_dir                        # ref enables later assets to reference this path

  - type: file
    path: "{{assets.issues_dir.rel_path}}/{{YY}}-{{MM}}-{{DD}}_{{slug}}-{{rand.str:6}}.md"
    template: issue.md                     # relative to this package dir

  - type: file
    when:
      expr: "with_tests"                   # Python expression; skipped if false
    path: "{{assets.issues_dir.rel_path}}/test-plan.md"
    content: |                             # inline content (alternative to template)
      # Test Plan for {{name}}

actions:
  - phase: post
    run: ["git", "status"]
    cwd: "{{project.root}}"
```

Template file (`issue.md`) lives in the same package directory:

```
.sprout/__new__/issue/
├── manifest.yaml
└── issue.md
```

---

## Bootstrap

```bash
sprout builtin <name>      # creates .sprout/__new__/<name>/manifest.yaml with commented template
```

Or create the directory and `manifest.yaml` manually.

---

## Project Config: `.sprout/config.yaml`

Two fields only:

```yaml
version: 1
conflict: fail   # fail | overwrite | skip | rename (optional, defaults to fail)
```

---

## Manifest Schema

### Top-level

| Field | Required | Description |
|-------|----------|-------------|
| `schema` | recommended | `sprout.manifest/v1`. Enables strict validation. Missing = legacy mode. Unknown = rejected. |
| `name` | yes | Command name (defaults to directory name if omitted) |
| `description` | yes | Human-readable description |
| `conflict` | no | `fail` \| `overwrite` \| `skip` \| `rename`. Overrides project config. |
| `inputs` | no | List of input field definitions |
| `computed` | no | List of derived variables (evaluated after inputs, before assets) |
| `assets` | no | List of files/dirs to generate |
| `actions` | no | List of post-generation commands |
| `root` | no | **Global mode only.** Base directory for relative asset paths (template string). |

### `inputs[*]`

| Field | Required | Description |
|-------|----------|-------------|
| `name` | yes | Unique identifier within this command |
| `type` | yes | `string` \| `number` \| `enum` \| `boolean` |
| `required` | no | Default `true` |
| `description` | no | Recommended |
| `default` | no | Supports `{{...}}` templates (e.g. `{{rand.str:6}}`) |
| `enum` | **if type=enum** | List of allowed string values |
| `min` / `max` | **number only** | Numeric bounds |

### `computed[*]`

| Field | Required | Description |
|-------|----------|-------------|
| `name` | yes | Must not duplicate any input name or built-in variable |
| `expr` | yes | Python expression. Context: all inputs + built-in time vars + earlier computed values |

Computed names become normal template variables: `{{slug}}`.

### `assets[*]`

| Field | Required | Description |
|-------|----------|-------------|
| `type` | yes | `dir` or `file` |
| `path` | yes | Relative path template. Project mode: must stay inside project root. |
| `template` | **file only** | Path to template file, relative to package dir |
| `content` | **file only** | Inline content string (alternative to `template`) |
| `ref` | no | Stable name for referencing this asset's path in later assets/actions |
| `when` | no | `{expr: "<python_expression>"}` — asset skipped if false |

**Source rules:**
- `file` → exactly one of `template` or `content` (never both, never neither)
- `dir` → neither `template` nor `content`
- Assets with `when.expr` evaluating to false are skipped entirely (no source validation, no ref registration)

### `actions[*]`

| Field | Required | Description |
|-------|----------|-------------|
| `phase` | yes | Currently only `post` |
| `run` | **one of** | Argv list: `["git", "init"]` — preferred |
| `shell` | **one of** | Shell string: `"echo hello"` |
| `cwd` | no | Working directory template. Relative paths resolve from project root. |

Exactly one of `run` / `shell` per action. Non-zero exit → `GenerationError`.

---

## Template Variables

`{{expression}}` syntax. Whitespace-tolerant (`{{ expr }}` = `{{expr}}`). Pure text substitution — no if/for/functions.

### Available Variables

| Category | Variables | Scope |
|----------|-----------|-------|
| **User inputs** | `{{name}}`, `{{type}}`, etc. | everywhere |
| **Computed** | `{{slug}}`, etc. | everywhere (after evaluation) |
| **Date/time** | `YYYY` `YY` `MM` `DD` `hh` `mm` `ss` `date` `time` `datetime` `timestamp` | everywhere |
| **Project mode** | `project.root` (posix abs), `project.root_name` (dir name) | assets, actions |
| **Global mode** | `home` (posix abs), `cwd` (posix abs), `platform` (`win32`/`darwin`/`linux`) | assets, actions |
| **Asset refs** | `assets.<ref>.<suffix>` | later assets and actions |
| **Random tokens** | `rand.str[:N]`, `rand.num[:N]` (default 8, max 128) | everywhere |

### Asset Ref Suffixes

| Suffix | Example value |
|--------|--------------|
| `abs_path` | `/home/user/project/issues` |
| `rel_path` | `issues` |
| `name` | `issues` |
| `parent_abs` | `/home/user/project` |
| `parent_rel` | `` (empty = root) |

### Scope Rules

- **Asset paths/templates**: use `assets.<ref>.<suffix>` (suffix required, bare ref forbidden)
- **Action templates**: bare `{{assets.<ref>}}` allowed, equals `abs_path`
- Asset refs only see **earlier** declared assets (forward reference forbidden)

---

## Conflict Resolution

Priority: `--conflict` CLI flag > manifest `conflict` > `config.yaml` > `fail`

| Policy | File exists | Dir exists |
|--------|-------------|------------|
| `fail` | **error** | reuse |
| `overwrite` | replace | reuse |
| `skip` | keep existing | reuse |
| `rename` | create with `_02` suffix | reuse |

File/dir type mismatch → unconditional error. Duplicate paths in same run → error.

---

## Global Mode Differences

Global commands live in `~/.config/sprout/__new__/`. Key differences from project mode:

| | Project mode | Global mode (`-g`) |
|---|---|---|
| Variables | `project.root`, `project.root_name` | `home`, `cwd`, `platform` |
| Asset paths | Must stay inside project root | Absolute allowed; relative resolves from `root` field or cwd |
| `root` field | Ignored | Declares base directory for relative paths |
| Legacy `commands/` | Supported | Not supported |

---

## Gotchas

1. **`file` asset without `template` or `content`** → validation error. Every file asset needs exactly one source.
2. **Forward ref in asset path** → `assets.<ref>` can only reference assets declared *before* this one.
3. **Bare `{{assets.ref}}` in asset path** → error. Must use `{{assets.ref.rel_path}}` or other suffix. Bare ref is only allowed in actions.
4. **`template` path is relative to package dir**, not project root. If manifest is at `.sprout/__new__/issue/manifest.yaml` and template is `issue.md`, the file must be at `.sprout/__new__/issue/issue.md`.
5. **`computed.name` shadowing input** → rejected. Computed names must not duplicate input names or built-in names.
6. **Missing `enum` list for `type: enum`** → validation error.
7. **`{{rand.str}}` generates different values each render** — two uses of `{{rand.str}}` in the same manifest produce different strings. Use `computed` to pin a random value for reuse.
8. **Relative paths in project mode are sandboxed** — path traversal beyond project root (`../`) is rejected.
9. **`when.expr` false → ref not registered** — later assets cannot reference a skipped asset's ref.
10. **`default` values are rendered as templates** — `default: "{{rand.str:6}}"` works; the template is evaluated at input collection time.

---

## Validation

After editing, verify with:

```bash
sprout doctor                              # check all manifests
sprout list --all                          # see valid + invalid + conflicting
sprout new <command> name=test --dry-run   # preview without creating files
```

Agent-friendly input (avoids shell escaping):

```bash
sprout new <command> --json '{"name":"test"}' --dry-run
sprout new <command> --json-file ./inputs.json --dry-run
```

---

## Checklist

Before finishing a command package, verify:

- [ ] Manifest at `.sprout/__new__/<name>/manifest.yaml`
- [ ] Every `file` asset has exactly one of `template` / `content`
- [ ] Template files exist in the package directory
- [ ] All `ref` values are unique within the command
- [ ] Asset-to-asset references only point backward (no forward refs)
- [ ] Asset path templates use explicit suffixes (`rel_path`, `abs_path`, etc.)
- [ ] Conflict policy set at command or project level
- [ ] Actions use `run` (argv) unless shell syntax is truly needed
- [ ] `sprout doctor` passes
- [ ] `sprout new <command> --dry-run` produces expected output
