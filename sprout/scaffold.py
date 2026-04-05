from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import InitReport, ValidationError


DEFAULT_CONFIG = {
    "version": 1,
    "conflict": "fail",
}


BUILTIN_PROFILES: dict[str, dict[str, Any]] = {
    "minimal": {
        "directories": [],
        "files": [
            {
                "path": "README.md",
                "content": "# .sprout workspace\n\nProject-local template command workspace for `sprout`.\n",
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
                    "Use `.sprout/commands/<name>/manifest.json` to define generators.\n"
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

Help users define or update command packages under `.sprout/commands/`.

## Core rule

Before editing files, align on:
1. Command purpose
2. Required inputs (`string` / `number` / `enum`)
3. Output assets (file/dir paths)
4. Conflict strategy (`fail/overwrite/skip/rename`)

Only write files after requirements are clear.

## Output checklist

For a command `<name>`, ensure:
- `.sprout/commands/<name>/manifest.json`
- Template files referenced by `assets[*].template`
- Paths use `{{variable}}` placeholders only (no control flow)
"""


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
    data = {
        "name": "issue",
        "description": "Create an issue document",
        "inputs": [
            {"name": "name", "type": "string", "description": "Issue slug"},
            {
                "name": "type",
                "type": "enum",
                "enum": ["bug", "feat", "refactor"],
                "default": "bug",
            },
        ],
        "assets": [
            {"type": "dir", "path": "issues"},
            {
                "type": "file",
                "path": "issues/{{YY}}-{{MM}}-{{DD}}_{{name}}.md",
                "template": "issue.md",
            },
        ],
    }
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def _example_change_manifest() -> str:
    data = {
        "name": "change",
        "description": "Create a change folder and proposal",
        "inputs": [
            {"name": "name", "type": "string", "description": "Change slug"},
            {
                "name": "type",
                "type": "enum",
                "enum": ["bug", "feat", "refactor"],
                "default": "feat",
            },
        ],
        "assets": [
            {"type": "dir", "path": "changes/{{YY}}-{{MM}}-{{DD}}_{{name}}"},
            {
                "type": "file",
                "path": "changes/{{YY}}-{{MM}}-{{DD}}_{{name}}/proposal.md",
                "template": "proposal.md",
            },
        ],
    }
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def _add_example_commands(commands_dir: Path, report: InitReport) -> None:
    issue_dir = commands_dir / "issue"
    change_dir = commands_dir / "change"

    _mkdir(issue_dir, report)
    _write_if_missing(issue_dir / "manifest.json", _example_issue_manifest(), report)
    _write_if_missing(
        issue_dir / "issue.md",
        "# Issue: {{name}}\n\n- Type: {{type}}\n- Date: {{date}}\n",
        report,
    )

    _mkdir(change_dir, report)
    _write_if_missing(change_dir / "manifest.json", _example_change_manifest(), report)
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
        sprout_dir / "config.json",
        json.dumps(DEFAULT_CONFIG, ensure_ascii=False, indent=2) + "\n",
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

    report.notes.append("Agent 协作建议：先对齐命令目的、输入字段和资产路径，再生成模板文件。")
    report.notes.append("本地 Skill 文档已放在 .sprout/skills/sprout-authoring/SKILL.md")

    return report
