from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import InitReport, ValidationError


def _get_templates_dir() -> Path:
    """Get the templates directory path."""
    return Path(__file__).parent / "templates"


def _load_builtin_profile(name: str) -> dict[str, Any]:
    """Load a built-in profile from templates/profiles/."""
    templates_dir = _get_templates_dir()
    profile_path = templates_dir / "profiles" / f"{name}.json"
    if not profile_path.exists():
        raise ValidationError(f"Built-in profile '{name}' not found")
    return json.loads(profile_path.read_text(encoding="utf-8"))


def _load_template_file(relative_path: str) -> str:
    """Load a template file from templates/."""
    templates_dir = _get_templates_dir()
    template_path = templates_dir / relative_path
    if not template_path.exists():
        raise ValidationError(f"Template file not found: {relative_path}")
    return template_path.read_text(encoding="utf-8")


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


def _copy_example_command(commands_dir: Path, example_name: str, report: InitReport) -> None:
    """Copy an example command package from templates/examples/."""
    templates_dir = _get_templates_dir()
    example_dir = templates_dir / "examples" / example_name
    
    if not example_dir.exists():
        raise ValidationError(f"Example command '{example_name}' not found")
    
    target_dir = commands_dir / example_name
    _mkdir(target_dir, report)
    
    # Copy all files from the example directory
    for file_path in example_dir.iterdir():
        if file_path.is_file():
            content = file_path.read_text(encoding="utf-8")
            _write_if_missing(target_dir / file_path.name, content, report)


def _add_example_commands(commands_dir: Path, report: InitReport) -> None:
    _copy_example_command(commands_dir, "issue", report)
    _copy_example_command(commands_dir, "task", report)


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

    # Write config.yaml from template
    config_content = _load_template_file("config.yaml")
    _write_if_missing(sprout_dir / "config.yaml", config_content, report)

    # Load profile
    if profile_file is not None:
        profile_data = _load_profile_from_file(profile_file)
    else:
        # List available built-in profiles
        templates_dir = _get_templates_dir()
        profiles_dir = templates_dir / "profiles"
        available_profiles = [p.stem for p in profiles_dir.glob("*.json")] if profiles_dir.exists() else []
        
        if profile not in available_profiles:
            raise ValidationError(
                f"Unknown profile '{profile}'. Available: {', '.join(sorted(available_profiles))}"
            )
        profile_data = _load_builtin_profile(profile)

    _apply_profile(sprout_dir, profile_data, report)

    # Write SKILL document from template
    skill_path = sprout_dir / "skills" / "sprout-authoring" / "SKILL.md"
    skill_content = _load_template_file("skill-authoring.md")
    _write_if_missing(skill_path, skill_content, report)

    if with_examples:
        _add_example_commands(commands_dir, report)

    report.notes.append("Agent 协作建议：先对齐命令目的、输入字段、输出资产与冲突策略，再生成模板文件。")
    report.notes.append("默认 authoring 格式已改为 YAML：先看 .sprout/config.yaml 与 commands/*/manifest.yaml。")
    report.notes.append("本地 Skill 文档已放在 .sprout/skills/sprout-authoring/SKILL.md")

    return report
