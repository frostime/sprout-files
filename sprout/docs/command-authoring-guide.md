# Sprout Command Authoring Guide

> How to create and maintain `.sprout/commands/*` command packages.

---

## Positioning

This guide is for **command package authors** and **Agents** that edit `.sprout/commands/*`.

It answers:

> How do I define or update Sprout command packages?

If you only need to **use** Sprout commands (`init`, `list`, `new`, `doctor`), read `user-guide` instead.

### Boundary from `user-guide`

- `user-guide`: how to use Sprout
- `command-authoring-guide`: how to write Sprout command packages

Rule of thumb:
- Content needed even when you never edit `.sprout/commands/*` → `user-guide`
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
- `.sprout/commands/<name>/manifest.yaml` — command definition
- Template files referenced by `assets[*].template`

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

## Command manifest: `.sprout/commands/<name>/manifest.yaml`

```yaml
name: issue
description: Create an issue document

# Optional per-command conflict override.
# If omitted, sprout uses `.sprout/config.yaml`.
conflict: fail

inputs:
  - name: name
    type: string
    required: true
    description: Issue slug used in file name

  - name: type
    type: enum
    enum:
      - bug
      - feat
      - refactor
    default: bug
    description: Issue category

  - name: priority
    type: number
    required: false
    min: 1
    max: 5
    default: 3
    description: Optional priority score

assets:
  - type: dir
    path: issues
    ref: issues_dir

  - type: file
    path: "{{assets.issues_dir.rel_path}}/{{YY}}-{{MM}}-{{DD}}_{{name}}-{{rand.str:6}}.md"
    template: issue.md
    ref: issue_file

actions:
  - phase: post
    run: ["git", "status"]
    cwd: "{{project.root}}"
```

---

## Field rules

### `inputs[*]`

- `name`: required, unique within the command
- `type`: `string` | `number` | `enum`
- `required`: optional, defaults to `true`
- `description`: optional but recommended
- `default`: optional
- `enum`: required when `type: enum`
- `min` / `max`: only for `type: number`

### `assets[*]`

- `type`: `dir` or `file`
- `path`: required relative path inside the project
- `template`: for file assets, path to template file inside the same command package
- `content`: optional inline content for simple files
- `ref`: optional stable name for later asset/action references

### `actions[*]`

- `phase`: currently only `post`
- `run`: preferred argv form, e.g. `["git", "init"]`
- `shell`: convenience shell string form
- `cwd`: optional working directory template
- exactly one of `run` / `shell`

---

## Rendering rules

- Placeholders use `{{...}}` only
- Supported variables = user inputs + built-in time values + project vars + asset refs + random tokens
- Asset path templates may reference only earlier asset refs, and should use explicit suffixes such as `{{assets.root_dir.rel_path}}`
- Action templates may use bare `{{assets.root_dir}}`, which means absolute path
- Random tokens: `{{rand.str}}`, `{{rand.str:10}}`, `{{rand.num}}`, `{{rand.num:6}}`
- No `if`, `for`, function calls, or nested logic
- Rendered paths must stay inside the project root and are normalized to `/` separators

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
