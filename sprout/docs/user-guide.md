# Sprout User Guide

> Template-driven file & directory generator for project workflows.

---

## Quick Start

```bash
# Initialize workspace in current project
sprout init --with-examples

# List available commands
sprout list

# Generate files from a command package
sprout new issue name=my-task type=bug

# Preview without creating files
sprout new issue name=test type=feat --dry-run
```

---

## Commands

### `sprout init`

Create a `.sprout/` workspace in the current directory.

```bash
sprout init                          # minimal scaffold
sprout init --profile docs           # includes doc templates
sprout init --with-examples          # adds example command packages (issue/task)
sprout init --profile-file ./p.json  # custom scaffold profile
```

### `sprout list`

Show discovered command packages.

```bash
sprout list        # valid commands only
sprout list --all  # include invalid/conflicting entries
```

### `sprout doctor`

Validate the command registry and report issues (invalid manifests, conflicts, template variable problems).

```bash
sprout doctor
```

### `sprout new <command>`

Generate files from a command package.

```bash
sprout new issue name=login type=feat
```

**Input methods** (can be combined, later sources override earlier):

| Method | Example |
|--------|---------|
| Positional `key=value` | `sprout new issue name=foo type=bug` |
| `--set key=value` | `sprout new issue --set name=foo --set type=bug` |
| `--json '{...}'` | `sprout new issue --json '{"name":"foo","type":"bug"}'` |
| `--json-file path` | `sprout new issue --json-file ./inputs.json` |

**Flags**:

| Flag | Effect |
|------|--------|
| `-i`, `--interactive` | Prompt for missing inputs (requires TTY) |
| `--no-input` | Disable all interactive prompts |
| `-n`, `--dry-run` | Show plan without creating files |
| `--conflict <policy>` | Override conflict policy for this run |

---

## Workspace Structure

```
.sprout/
├── config.yaml          # Project-level defaults
└── commands/
    └── issue/
        ├── manifest.yaml  # Command definition
        └── issue.md       # Template file
```

### `config.yaml`

```yaml
version: 1
conflict: fail    # fail | overwrite | skip | rename
```

### `manifest.yaml`

A manifest defines a command's inputs, outputs, and optional post-actions.

```yaml
name: issue
description: Create an issue file

conflict: fail   # optional per-command override

inputs:
  - name: name
    type: string
    required: true
    description: Issue slug

  - name: type
    type: enum
    enum: [bug, feat, refactor]
    default: bug

  - name: priority
    type: number
    required: false
    min: 1
    max: 5
    default: 3

assets:
  - type: dir
    path: issues
    ref: issues_dir

  - type: file
    path: "{{assets.issues_dir.rel_path}}/{{YY}}-{{MM}}-{{DD}}_{{name}}.md"
    template: issue.md
    ref: issue_file

actions:
  - phase: post
    run: ["git", "status"]
    cwd: "{{project.root}}"
```

#### Input types

| Type | Fields |
|------|--------|
| `string` | `name`, `required`, `default`, `description` |
| `number` | `name`, `required`, `default`, `description`, `min`, `max` |
| `enum` | `name`, `required`, `default`, `description`, `enum` (list of choices) |

#### Asset types

| Type | Fields |
|------|--------|
| `dir` | `path`, `ref` (optional) |
| `file` | `path`, `template` or `content`, `ref` (optional) |

- `template`: path relative to the command directory
- `content`: inline string (mutually exclusive with `template`)
- `ref`: name for cross-referencing in later assets or actions

#### Actions

| Field | Description |
|-------|-------------|
| `phase` | Currently only `post` |
| `run` | Command as argument array (recommended) |
| `shell` | Command as single shell string |
| `cwd` | Working directory (supports variables, must be within project root) |

`run` and `shell` are mutually exclusive.

---

## Template Variables

### User inputs

All `inputs[*].name` values are available directly: `{{name}}`, `{{type}}`, etc.

### Built-in time variables

| Variable | Example |
|----------|---------|
| `{{YYYY}}` | 2026 |
| `{{YY}}` | 26 |
| `{{MM}}` | 04 |
| `{{DD}}` | 12 |
| `{{hh}}` | 14 |
| `{{mm}}` | 30 |
| `{{ss}}` | 05 |
| `{{date}}` | 2026-04-12 |
| `{{time}}` | 14:30:05 |
| `{{datetime}}` | 2026-04-12T14:30:05 |
| `{{timestamp}}` | 1744451405 |

### Project variables

| Variable | Description |
|----------|-------------|
| `{{project.root}}` | Absolute path to project root |
| `{{project.root_name}}` | Name of the root directory |

### Random variables

| Variable | Description |
|----------|-------------|
| `{{rand.str}}` | 8-char alphanumeric string |
| `{{rand.str:N}}` | N-char alphanumeric string |
| `{{rand.num}}` | 8-digit number string |
| `{{rand.num:N}}` | N-digit number string |

### Asset reference variables

When an asset has `ref: foo`, later assets and actions can use:

| Variable | Description |
|----------|-------------|
| `{{assets.foo.abs_path}}` | Absolute path |
| `{{assets.foo.rel_path}}` | Relative path from project root |
| `{{assets.foo.name}}` | File/dir name |
| `{{assets.foo.parent_abs}}` | Parent absolute path |
| `{{assets.foo.parent_rel}}` | Parent relative path |

In `actions[*]`, `{{assets.foo}}` is shorthand for `{{assets.foo.abs_path}}`.

In `assets[*].path`, only refs defined in earlier assets can be referenced.

---

## Conflict Policies

When a generated file already exists:

| Policy | Behavior |
|--------|----------|
| `fail` | Error and stop (default) |
| `skip` | Leave existing file untouched |
| `overwrite` | Replace existing file |
| `rename` | Create with suffix `_02`, `_03`, ... |

Directories are always reused — conflict policies apply to files only.

Priority: `--conflict` flag > manifest `conflict` > `config.yaml` `conflict` > `fail`.

---

## Interactive Mode

- **TTY + missing inputs**: sprout shows which fields are missing, then asks whether to enter interactive mode
- **TTY + `-i` flag**: goes straight to interactive prompts
- **Non-TTY + missing inputs**: fails immediately (won't block scripts/agents)
- **Non-TTY + `-i` flag**: errors with "Interactive mode requires a TTY"

During interactive prompts, type `q`, `quit`, or `exit` to cancel.

---

## Tips

- Use `sprout doctor` to diagnose manifest or template issues
- Prefer `--json` or `--json-file` for complex inputs (spaces, special chars)
- Combine `--json` with `--set` to override specific fields
- Use `--dry-run` to preview before generating
- All path separators in variable output use `/`
