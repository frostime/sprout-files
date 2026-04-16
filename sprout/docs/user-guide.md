# Sprout User Guide

> How to use the `sprout` CLI to initialize workspaces, inspect commands, generate files, and troubleshoot runs.

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

## Positioning

This guide is for people who want to **use** Sprout.

It answers:

> How do I run `sprout init`, `sprout list`, `sprout doctor`, and `sprout new`?

If you need to create or maintain `.sprout/__new__/*` command packages (runtime also reads legacy `.sprout/commands/*`), read:

```bash
sprout doc show command-authoring-guide
```

You can also inspect built-in docs with:

```bash
sprout doc list
sprout doc path user-guide
sprout doc path command-authoring-guide
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

### `sprout init --global`

Create a global sprout directory at `~/.config/sprout/`. See [Global Mode](#global-mode) for details.

```bash
sprout init --global
```

### `sprout list`

Show discovered command packages.

```bash
sprout list        # valid commands only
sprout list --all  # include invalid/conflicting entries
sprout list -g    # list global commands
```

### `sprout doctor`

Validate the command registry and report issues (invalid manifests, conflicts, template variable problems).

```bash
sprout doctor      # project commands
sprout doctor -g   # global commands
```

### `sprout builtin <name>`

Create a commented starter manifest for a new command package.

```bash
sprout builtin demo
sprout buildin demo   # compatibility alias
```

By default this creates:

```text
.sprout/__new__/demo/manifest.yaml
```

If a legacy `.sprout/commands/` directory exists, sprout will migrate or merge safe subdirectories into `.sprout/__new__/` before writing the new manifest.

### `sprout doc`

Show built-in documentation.

```bash
sprout doc list
sprout doc show user-guide
sprout doc show command-authoring-guide
sprout doc path command-authoring-guide
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
| `-g`, `--global` | Use global sprout directory (~/.config/sprout/) |

---

## Global Mode

Sprout can operate in **global mode** to create files anywhere on your system — outside any project. This is useful for personal workflow shortcuts like creating temporary directories, notes, or workspace scaffolds.

### Setup

```bash
sprout init --global
```

This creates `~/.config/sprout/` with a `config.yaml` and `__new__/` directory for global commands.

### Global Command Structure

```
~/.config/sprout/
├── config.yaml
└── __new__/
    └── <command>/
        └── manifest.yaml
```

Global commands support all manifest features, plus:

- **`root` field** — optional; declares the base directory for relative asset paths
  - Supports template variables: `root: "{{home}}/temp"`
  - Without `root`, asset paths resolve relative to the current working directory
- **Global template variables**: `{{home}}`, `{{cwd}}`, `{{platform}}`
- **Absolute paths** — global assets may render to absolute paths (e.g., `{{home}}/Downloads/note.md`)

### Example: Temp Directory Command

```yaml
# ~/.config/sprout/__new__/temp/manifest.yaml
name: temp
description: Create a temporary directory
root: "{{home}}/temp"
inputs:
  - name: name
    type: string
    default: "temp-{{rand.str:6}}"
assets:
  - type: dir
    path: "{{name}}"
    ref: target
actions:
  - phase: post
    shell: 'echo "Created: {{assets.target.abs_path}}"'
```

```bash
sprout new -g temp              # creates ~/temp/temp-xxxxxx
sprout new -g temp name=myproj  # creates ~/temp/myproj
```

### Example: Quick Note Command (no root)

```yaml
# ~/.config/sprout/__new__/note/manifest.yaml
name: note
description: Create a quick note in the current directory
inputs:
  - name: title
    type: string
assets:
  - type: file
    path: "{{title}}.md"
    content: "# {{title}}\n\nCreated at {{datetime}}\n"
```

```bash
cd ~/Desktop
sprout new -g note title=idea
# creates ~/Desktop/idea.md
```

### Key Differences from Project Mode

| | Project mode (default) | Global mode (`-g`) |
|---|---|---|
| Registry | `.sprout/` in project | `~/.config/sprout/` |
| Asset paths | Relative to project root | Relative to `root` or cwd |
| Absolute paths | Not allowed | Allowed |
| Template variables | `project.root`, `project.root_name` | `home`, `cwd`, `platform` |

---

## Workspace Structure

```
.sprout/
├── config.yaml
├── __new__/
│   └── <command>/
│       ├── manifest.yaml
│       └── <template files>
└── commands/   # legacy layout, still readable
```

This is the preferred workspace layout. Runtime discovery reads both `__new__/` and legacy `commands/`.

If you need the full manifest schema, variable reference, or command package authoring rules, use:

```bash
sprout doc show command-authoring-guide
```

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
- To inspect packaged documentation, use `sprout doc list`
- Use `sprout new -g <command>` to run global commands from any directory
