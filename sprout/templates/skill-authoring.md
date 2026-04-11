---
name: sprout-authoring
description: Use this guide when creating/updating `.sprout/commands/*` command packages for this project.
---

# sprout-authoring

## Intent

Help users and Agents define or update command packages under `.sprout/commands/`.

## First align before editing

Before writing any file, confirm these 4 things with the user:
1. **Command purpose**: What should `sprout new <command>` create?
2. **Inputs**: Which fields are required? What type is each field?
3. **Assets**: Which files/directories should be generated? Where?
4. **Conflict policy**: What should happen if the target already exists? (`fail` / `overwrite` / `skip` / `rename`)

If any of these are unclear, ask first. Do not guess package structure.

## Files to create or edit

For command `<name>`, usually touch:
- `.sprout/config.yaml` — project-level defaults such as `conflict`
- `.sprout/commands/<name>/manifest.yaml` — command definition
- Template files referenced by `assets[*].template`

## Data model quick reference

### 1) Project config: `.sprout/config.yaml`

```yaml
# sprout project defaults
version: 1

# Default target conflict policy for generated assets.
# Allowed: fail | overwrite | skip | rename
conflict: fail
```

- `version`: integer, current value is `1`
- `conflict`: optional project default, one of `fail`, `overwrite`, `skip`, `rename`

### 2) Command manifest: `.sprout/commands/<name>/manifest.yaml`

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

  - type: file
    path: issues/{{YY}}-{{MM}}-{{DD}}_{{name}}.md
    template: issue.md
```

## Field filling rules

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

## Rendering rules

- Placeholders use `{{variable}}` only
- Supported variables = user inputs + built-in time values:
  `YYYY`, `YY`, `MM`, `DD`, `hh`, `mm`, `ss`, `date`, `time`, `datetime`, `timestamp`
- No `if`, `for`, function calls, or nested logic
- Paths must stay inside the project root

## Authoring checklist

Before finishing, verify:
- manifest file path is correct
- every input has a clear purpose
- every file asset has either `template` or `content`
- template files actually exist
- paths only use `{{var}}` interpolation
- conflict behavior is explicit somewhere (command or project level)

## Validation commands

After editing, run:

```bash
sprout doctor
sprout list --all
sprout new <command> ...
```
