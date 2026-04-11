from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import InitReport, ValidationError


BUILTIN_PROFILES: dict[str, dict[str, Any]] = {
    "minimal": {
        "directories": [],
        "files": [
            {
                "path": "README.md",
                "content": (
                    "# .sprout workspace\n\n"
                    "Project-local template command workspace for `sprout`.\n\n"
                    "Start with `.sprout/config.yaml` and `.sprout/commands/<name>/manifest.yaml`.\n"
                ),
            }
        ],
    },
    "docs": {
        "directories": ["profiles"],
        "files": [
            {
                "path": "README.md",
                "content": (
                    "# .sprout workspace\n\n"
                    "Use `.sprout/config.yaml` for project defaults and `"
                    "`.sprout/commands/<name>/manifest.yaml` to define generators.\n"
                ),
            },
            {
                "path": "profiles/default.json",
                "content": json.dumps(
                    {
                        "name": "default",
                        "notes": "Example profile metadata for team conventions.",
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
            },
        ],
    },
}


LOCAL_SKILL_CONTENT = """---
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
"""


def _default_config_yaml() -> str:
    return (
        "# sprout project defaults\n"
        "version: 1\n\n"
        "# Default conflict policy for generated files/directories.\n"
        "# Allowed: fail | overwrite | skip | rename\n"
        "conflict: fail\n"
    )


def _safe_target(base: Path, relative_path: str) -> Path:
    candidate = (base / relative_path).resolve(strict=False)
    base_resolved = base.resolve()
    if candidate == base_resolved:
        return candidate
    if base_resolved not in candidate.parents:
        raise ValidationError(f"Scaffold path escapes .sprout workspace: {relative_path}")
    return candidate


def _mkdir(path: Path, report: InitReport) -> None:
    if path.exists():
        report.skipped.append(path)
        return
    path.mkdir(parents=True, exist_ok=True)
    report.created.append(path)


def _write_if_missing(path: Path, content: str, report: InitReport) -> None:
    if path.exists():
        report.skipped.append(path)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    report.created.append(path)


def _load_profile_from_file(path: Path) -> dict[str, Any]:
    if not path.exists() or not path.is_file():
        raise ValidationError(f"Profile file not found: {path}")

    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValidationError("Profile file must be a JSON object")

    directories = data.get("directories", [])
    files = data.get("files", [])
    if not isinstance(directories, list) or not isinstance(files, list):
        raise ValidationError("Profile file fields 'directories' and 'files' must be lists")

    return data


def _apply_profile(sprout_dir: Path, profile_data: dict[str, Any], report: InitReport) -> None:
    directories = profile_data.get("directories", [])
    files = profile_data.get("files", [])

    for item in directories:
        if not isinstance(item, str):
            raise ValidationError("Profile directories must contain string paths")
        _mkdir(_safe_target(sprout_dir, item), report)

    for file_item in files:
        if not isinstance(file_item, dict):
            raise ValidationError("Profile files must contain objects with path/content")
        rel_path = file_item.get("path")
        content = file_item.get("content", "")
        if not isinstance(rel_path, str) or not rel_path.strip():
            raise ValidationError("Profile file entry requires non-empty string 'path'")
        _write_if_missing(_safe_target(sprout_dir, rel_path), str(content), report)


def _example_issue_manifest() -> str:
    return """name: issue
description: Create an issue document

# Optional command-level conflict override.
# If omitted, sprout uses `.sprout/config.yaml`.
# conflict: fail

inputs:
  - name: name
    type: string
    description: Issue slug used in generated file names

  - name: type
    type: enum
    enum:
      - bug
      - feat
      - refactor
    default: bug
    description: Issue category

assets:
  - type: dir
    path: issues

  - type: file
    path: issues/{{YY}}-{{MM}}-{{DD}}_{{name}}.md
    template: issue.md
"""


def _example_change_manifest() -> str:
    return """name: change
description: Create a change folder and proposal

inputs:
  - name: name
    type: string
    description: Change slug

  - name: type
    type: enum
    enum:
      - bug
      - feat
      - refactor
    default: feat
    description: Change category

assets:
  - type: dir
    path: changes/{{YY}}-{{MM}}-{{DD}}_{{name}}

  - type: file
    path: changes/{{YY}}-{{MM}}-{{DD}}_{{name}}/proposal.md
    template: proposal.md
"""


def _add_example_commands(commands_dir: Path, report: InitReport) -> None:
    issue_dir = commands_dir / "issue"
    change_dir = commands_dir / "change"

    _mkdir(issue_dir, report)
    _write_if_missing(issue_dir / "manifest.yaml", _example_issue_manifest(), report)
    _write_if_missing(
        issue_dir / "issue.md",
        "# Issue: {{name}}\n\n- Type: {{type}}\n- Date: {{date}}\n",
        report,
    )

    _mkdir(change_dir, report)
    _write_if_missing(change_dir / "manifest.yaml", _example_change_manifest(), report)
    _write_if_missing(
        change_dir / "proposal.md",
        "# Change: {{name}}\n\n- Type: {{type}}\n- Created: {{datetime}}\n",
        report,
    )


def initialize_workspace(
    project_root: Path,
    *,
    profile: str,
    profile_file: Path | None,
    with_examples: bool,
) -> InitReport:
    report = InitReport()

    sprout_dir = project_root / ".sprout"
    commands_dir = sprout_dir / "commands"

    _mkdir(sprout_dir, report)
    _mkdir(commands_dir, report)

    _write_if_missing(
        sprout_dir / "config.yaml",
        _default_config_yaml(),
        report,
    )

    if profile_file is not None:
        profile_data = _load_profile_from_file(profile_file)
    else:
        if profile not in BUILTIN_PROFILES:
            raise ValidationError(
                f"Unknown profile '{profile}'. Available: {', '.join(sorted(BUILTIN_PROFILES))}"
            )
        profile_data = BUILTIN_PROFILES[profile]

    _apply_profile(sprout_dir, profile_data, report)

    skill_path = sprout_dir / "skills" / "sprout-authoring" / "SKILL.md"
    _write_if_missing(skill_path, LOCAL_SKILL_CONTENT, report)

    if with_examples:
        _add_example_commands(commands_dir, report)

    report.notes.append("Agent 协作建议：先对齐命令目的、输入字段、输出资产与冲突策略，再生成模板文件。")
    report.notes.append("默认 authoring 格式已改为 YAML：先看 .sprout/config.yaml 与 commands/*/manifest.yaml。")
    report.notes.append("本地 Skill 文档已放在 .sprout/skills/sprout-authoring/SKILL.md")

    return report
