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

If you need to create or maintain `.sprout/commands/*`, read:

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

---

## Workspace Structure

```
.sprout/
├── config.yaml
└── commands/
    └── <command>/
        ├── manifest.yaml
        └── <template files>
```

This is the runtime workspace layout.

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
