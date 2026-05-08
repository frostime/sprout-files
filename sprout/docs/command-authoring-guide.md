# Sprout Command Authoring Guide

> How to create and maintain `.sprout/__new__/*` command packages (runtime also reads legacy `.sprout/commands/*`).

---

## Positioning

This guide is for **command package authors** and **Agents** that edit `.sprout/__new__/*`.

It answers:

> How do I define or update Sprout command packages?

If you only need to **use** Sprout commands (`init`, `list`, `new`, `doctor`), read `user-guide` instead.

### Boundary from `user-guide`

- `user-guide`: how to use Sprout
- `command-authoring-guide`: how to write Sprout command packages

Rule of thumb:
- Content needed even when you never edit `.sprout/__new__/*` → `user-guide`
- Content needed only when creating or maintaining command packages → this guide

---

## First align before editing

Before writing any file, confirm these 4 things:

1. **Command purpose**: What should `sprout new <command>` create?
2. **Inputs**: Which fields are required? What type is each field?
3. **Assets**: Which files/directories should be generated? Where?
4. **Conflict policy**: What should happen if the target already exists? (`fail` / `overwrite` / `skip` / `rename`)

If any of these are unclear, ask first. Do not guess package structure.

---

## Files to create or edit

For command `<name>`, usually touch:

- `.sprout/config.yaml` — project-level defaults such as `conflict`
- `.sprout/__new__/<name>/manifest.yaml` — preferred command definition path
- Template files referenced by `assets[*].template`

Quick bootstrap:

```bash
sprout builtin <name>
sprout buildin <name>   # compatibility alias
```

---

## Project config: `.sprout/config.yaml`

```yaml
# sprout project defaults
version: 1

# Default target conflict policy for generated assets.
# Allowed: fail | overwrite | skip | rename
conflict: fail
```

- `version`: integer, current value is `1`
- `conflict`: optional project default, one of `fail`, `overwrite`, `skip`, `rename`

---

## Command manifest: `.sprout/__new__/<name>/manifest.yaml`

```yaml
schema: sprout.manifest/v1

name: issue
description: Create an issue document

# Optional per-command conflict override.
# If omitted, sprout uses `.sprout/config.yaml`.
conflict: fail

inputs:
  - name: name
    type: string
    required: true
    description: Issue title used in generated content

  - name: type
    type: enum
    enum:
      - bug
      - feat
      - refactor
    default: bug
    description: Issue category

  - name: with_tests
    type: boolean
    default: false
    description: Whether to create a test plan

computed:
  - name: slug
    expr: "name.strip().lower().replace(' ', '-')"

assets:
  - type: dir
    path: issues/{{slug}}
    ref: issues_dir

  - type: file
    path: "{{assets.issues_dir.rel_path}}/{{YY}}-{{MM}}-{{DD}}_{{slug}}-{{rand.str:6}}.md"
    template: issue.md
    ref: issue_file

  - type: file
    when:
      expr: "with_tests"
    path: "{{assets.issues_dir.rel_path}}/test-plan.md"
    content: |
      # Test Plan for {{name}}

actions:
  - phase: post
    run: ["git", "status"]
    cwd: "{{project.root}}"
```

---

## Field rules

### Top-level `schema`

- `schema: sprout.manifest/v1` enables the current explicit manifest grammar
- Missing `schema` remains compatible with legacy manifests
- Unknown schema values are rejected for that command package

### `inputs[*]`

- `name`: required, unique within the command
- `type`: `string` | `number` | `enum` | `boolean`
- `required`: optional, defaults to `true`
- `description`: optional but recommended
- `default`: optional; supports `{{...}}` template expressions (e.g. `{{rand.str:6}}`, `{{YYYY}}-{{MM}}`)
- `enum`: required when `type: enum`
- `min` / `max`: only for `type: number`

### `computed[*]`

- Optional list evaluated after inputs and before assets
- Each entry has `name` and `expr`
- `expr` is a Python expression evaluated against inputs, built-in time variables, and earlier computed values
- Computed names become normal template variables, e.g. `path: "{{slug}}.md"`
- Computed names must not duplicate inputs or reserved built-in names

### `assets[*]`

- `type`: `dir` or `file`
- `path`: relative path inside the project (project mode) or any path (global mode)
- `template`: for file assets, path to template file inside the same command package
- `content`: optional inline content for simple files
- `ref`: optional stable name for later asset/action references
- `when`: optional condition object, currently `when: {expr: "..."}`

Active asset source rules:
- `file` assets must define exactly one of `template` or `content`
- `dir` assets must define neither `template` nor `content`
- assets with `when.expr` evaluating to false are skipped before source validation and ref registration

### `actions[*]`

- `phase`: currently only `post`
- `run`: preferred argv form, e.g. `["git", "init"]`
- `shell`: convenience shell string form
- `cwd`: optional working directory template
- exactly one of `run` / `shell`

### `root` (global mode only)

- Optional field declaring the base directory for relative asset paths
- Supports template variables: `root: "{{home}}/temp"`
- If omitted, relative asset paths resolve from the current working directory
- Only meaningful in global mode; ignored in project mode

---

## Rendering and expression rules

- `{{...}}` means text interpolation only
- `expr: "..."` means Python expression evaluation in `computed[*].expr` and `assets[*].when.expr`
- Project mode variables = user inputs + computed values + built-in time values + `project.root` / `project.root_name` + asset refs + random tokens
- Global mode variables = user inputs + computed values + built-in time values + `home` / `cwd` / `platform` + asset refs + random tokens
- `inputs[*].default` values are also rendered as templates (e.g. `default: "{{rand.str:6}}"`)
- Asset path templates may reference only earlier active asset refs, and should use explicit suffixes such as `{{assets.root_dir.rel_path}}`
- Action templates may use bare `{{assets.root_dir}}`, which means absolute path
- Random tokens: `{{rand.str}}`, `{{rand.str:10}}`, `{{rand.num}}`, `{{rand.num:6}}`
- Template interpolation has no `if`, `for`, function calls, or nested logic; use `computed[*].expr` / `when.expr` for Python expressions
- In **project mode**: rendered paths must stay inside the project root and are normalized to `/` separators
- In **global mode**: rendered paths may be absolute; relative paths resolve from the `root` field or cwd

---

## Authoring checklist

Before finishing, verify:

- manifest file path is correct
- every input has a clear purpose
- every file asset has either `template` or `content`
- template files actually exist
- any `ref` values are unique within the command
- asset-to-asset references only point backward
- conflict behavior is explicit somewhere (command or project level)
- action commands use `run` unless shell syntax is truly more ergonomic

---

## Validation commands

After editing, run:

```bash
sprout doctor
sprout list --all
sprout new <command> name=test
sprout new <command> --json '{"name":"test"}'
sprout new <command> name=test --dry-run
```

---

## Runtime input guidance

- Human-friendly quick path: `sprout new <command> name=value ...`
- Agent / script-friendly path: `sprout new <command> --json '{...}'`
- Most reliable structured input path: `sprout new <command> --json-file ./inputs.json`
- `--set key=value` can override values provided by `--json` / `--json-file`
- If required inputs are missing, sprout only offers interactive fill-in when running in a TTY
- In non-TTY environments, missing required inputs fail fast instead of waiting for input
- Use `--no-input` to explicitly disable all interactive prompts
- In interactive prompts, `q`, `quit`, `exit`, or `Ctrl+C` cancels the run

## Compatibility note

- Preferred authoring directory: `.sprout/__new__/`
- Legacy directory still read at runtime: `.sprout/commands/`
- When sprout writes new built-in scaffolds or initializes a workspace, it prefers `__new__/` and migrates safe legacy subdirectories automatically

## Global mode

Global commands live in `~/.config/sprout/__new__/` and are available everywhere, not tied to any project. Create the global directory with:

```bash
sprout init --global
```

Global manifests support the same fields as project manifests, plus:

- **`root`** — optional base directory for relative asset paths (supports template variables)
- No `commands/` legacy directory — global mode only reads `__new__/`

Global mode provides `{{home}}`, `{{cwd}}`, and `{{platform}}` instead of `{{project.root}}` and `{{project.root_name}}`.

Absolute paths are allowed in global mode — assets like `{{home}}/Downloads/note.md` work naturally.

See the user guide (`sprout doc show user-guide`) for global mode examples.
