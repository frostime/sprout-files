from __future__ import annotations

import json
import re
import secrets
import string
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Literal

from .models import (
    ActionSpec,
    AssetSpec,
    CommandIssue,
    CommandRegistry,
    CommandSpec,
    ConflictPolicy,
    DiscoveryError,
    GenerationError,
    GeneratedItem,
    InputSpec,
    ProjectConfig,
    TemplateValidationIssue,
    UserAbortError,
    ValidationError,
)

MANIFEST_NAMES = (
    'manifest.yaml',
    'manifest.yml',
    'manifest.json',
)
CONFIG_NAMES = (
    'config.yaml',
    'config.yml',
    'config.json',
)

VALID_INPUT_TYPES = {'string', 'number', 'enum'}
VALID_ASSET_TYPES = {'file', 'dir'}
VALID_CONFLICT_POLICIES = {'fail', 'overwrite', 'skip', 'rename'}
VALID_ACTION_PHASES = {'post'}
VALID_ASSET_SUFFIXES = {'abs_path', 'rel_path', 'name', 'parent_abs', 'parent_rel'}
PLACEHOLDER_PATTERN = re.compile(r'\{\{\s*([^{}]+?)\s*\}\}')
IDENTIFIER_PATTERN = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')
ASSET_EXPR_PATTERN = re.compile(
    r'^assets\.([A-Za-z_][A-Za-z0-9_]*)(?:\.(abs_path|rel_path|name|parent_abs|parent_rel))?$'
)
RAND_EXPR_PATTERN = re.compile(r'^rand\.(str|num)(?::([1-9][0-9]*))?$')
CANCEL_INPUTS = {'q', 'quit', 'exit'}
DEFAULT_RANDOM_LENGTH = 8
MAX_RANDOM_LENGTH = 128

# Built-in template variables
BUILTIN_VARIABLES = {
    'YYYY', 'YY', 'MM', 'DD',
    'hh', 'mm', 'ss',
    'date', 'time', 'datetime', 'timestamp',
}
PROJECT_VARIABLES = {'project.root', 'project.root_name'}
PREFERRED_COMMANDS_DIRNAME = '__new__'
LEGACY_COMMANDS_DIRNAME = 'commands'


@dataclass(slots=True)
class PlannedAsset:
    index: int
    asset: AssetSpec
    requested_path: str
    target_path: Path
    final_path: Path
    action: str
    content: str | None


@dataclass(slots=True)
class PlannedAction:
    index: int
    mode: Literal['argv', 'shell']
    command_display: str
    cwd: Path | None
    argv: list[str] | None = None
    shell_command: str | None = None


@dataclass(slots=True)
class PromptInfo:
    title: str
    description: str
    detail: str


# ================================================
# Section: Project and manifest loading
# ================================================


def discover_project_root(start: Path, directory_name: str = '.sprout') -> Path:
    current = start.resolve()
    while True:
        if (current / directory_name).is_dir():
            return current
        if current.parent == current:
            break
        current = current.parent
    raise DiscoveryError(
        "No project template root found. Expected '.sprout/' in current directory or ancestors."
    )


def authoring_directories(sprout_dir: Path) -> tuple[Path, Path]:
    return sprout_dir / PREFERRED_COMMANDS_DIRNAME, sprout_dir / LEGACY_COMMANDS_DIRNAME


def iter_command_package_dirs(sprout_dir: Path) -> list[Path]:
    preferred_dir, legacy_dir = authoring_directories(sprout_dir)
    package_dirs: list[Path] = []

    for commands_dir in (preferred_dir, legacy_dir):
        if not commands_dir.exists() or not commands_dir.is_dir():
            continue
        for child in sorted(commands_dir.iterdir()):
            if child.is_dir():
                package_dirs.append(child)

    return package_dirs


def _load_mapping_file(path: Path) -> dict[str, Any]:
    suffix = path.suffix.lower()

    if suffix == '.json':
        data = json.loads(path.read_text(encoding='utf-8'))
    elif suffix in {'.yaml', '.yml'}:
        try:
            import yaml  # type: ignore
        except ModuleNotFoundError as exc:
            raise ValidationError(
                f"{path}: YAML support requires PyYAML. "
                f"Install with: uv add --optional yaml  OR  pip install pyyaml"
            ) from exc
        data = yaml.safe_load(path.read_text(encoding='utf-8'))
    else:
        raise ValidationError(f'Unsupported file format: {path}')

    if not isinstance(data, dict):
        raise ValidationError(f'{path}: expected a mapping/object at top-level')
    return data


def _config_path_for(sprout_dir: Path) -> Path | None:
    for filename in CONFIG_NAMES:
        candidate = sprout_dir / filename
        if candidate.exists() and candidate.is_file():
            return candidate
    return None


def _read_project_config(sprout_dir: Path) -> ProjectConfig:
    config_path = _config_path_for(sprout_dir)
    if config_path is None:
        return ProjectConfig()

    data = _load_mapping_file(config_path)
    conflict = str(data.get('conflict', 'fail'))
    if conflict not in VALID_CONFLICT_POLICIES:
        raise ValidationError(
            f'{config_path}: conflict must be one of {sorted(VALID_CONFLICT_POLICIES)}'
        )

    version = data.get('version', 1)
    if not isinstance(version, int):
        raise ValidationError(f'{config_path}: version must be integer')

    return ProjectConfig(version=version, conflict=conflict)  # type: ignore[arg-type]


def _manifest_path_for(package_dir: Path) -> Path:
    for filename in MANIFEST_NAMES:
        candidate = package_dir / filename
        if candidate.exists() and candidate.is_file():
            return candidate
    raise ValidationError(
        f"{package_dir}: missing manifest file. Expected one of: {', '.join(MANIFEST_NAMES)}"
    )


def _as_bool(value: Any, *, default: bool = True) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {'1', 'true', 'yes', 'y', 'on'}:
            return True
        if normalized in {'0', 'false', 'no', 'n', 'off'}:
            return False
    raise ValidationError(f'Invalid boolean value: {value!r}')


def _parse_input_spec(raw: Any, manifest_path: Path, index: int) -> InputSpec:
    if not isinstance(raw, dict):
        raise ValidationError(
            f'{manifest_path}: inputs[{index}] must be an object, got {type(raw).__name__}'
        )

    name = raw.get('name')
    if not isinstance(name, str) or not name.strip():
        raise ValidationError(f'{manifest_path}: inputs[{index}].name must be a non-empty string')

    input_type = str(raw.get('type', 'string'))
    if input_type not in VALID_INPUT_TYPES:
        raise ValidationError(
            f'{manifest_path}: inputs[{index}].type must be one of {sorted(VALID_INPUT_TYPES)}'
        )

    required = _as_bool(raw.get('required', True), default=True)
    description = str(raw.get('description', ''))
    default = raw.get('default')

    enum_values: list[str] = []
    minimum: float | None = None
    maximum: float | None = None

    if input_type == 'enum':
        enum_raw = raw.get('enum', raw.get('choices', []))
        if not isinstance(enum_raw, list) or not enum_raw:
            raise ValidationError(
                f'{manifest_path}: inputs[{index}] enum/choices must be a non-empty list'
            )
        enum_values = [str(item) for item in enum_raw]

    if input_type == 'number':
        min_raw = raw.get('min')
        max_raw = raw.get('max')
        if min_raw is not None:
            try:
                minimum = float(min_raw)
            except (TypeError, ValueError) as exc:
                raise ValidationError(
                    f'{manifest_path}: inputs[{index}].min must be a number'
                ) from exc
        if max_raw is not None:
            try:
                maximum = float(max_raw)
            except (TypeError, ValueError) as exc:
                raise ValidationError(
                    f'{manifest_path}: inputs[{index}].max must be a number'
                ) from exc
        if minimum is not None and maximum is not None and minimum > maximum:
            raise ValidationError(
                f'{manifest_path}: inputs[{index}] has min > max ({minimum} > {maximum})'
            )

    return InputSpec(
        name=name.strip(),
        type=input_type,  # type: ignore[arg-type]
        required=required,
        description=description,
        default=default,
        enum=enum_values,
        minimum=minimum,
        maximum=maximum,
    )


def _parse_asset_spec(raw: Any, manifest_path: Path, index: int) -> AssetSpec:
    if not isinstance(raw, dict):
        raise ValidationError(
            f'{manifest_path}: assets[{index}] must be an object, got {type(raw).__name__}'
        )

    asset_type = str(raw.get('type', ''))
    if asset_type not in VALID_ASSET_TYPES:
        raise ValidationError(
            f'{manifest_path}: assets[{index}].type must be one of {sorted(VALID_ASSET_TYPES)}'
        )

    path = raw.get('path', raw.get('asset'))
    if not isinstance(path, str) or not path.strip():
        raise ValidationError(f'{manifest_path}: assets[{index}].path must be a non-empty string')

    template = raw.get('template')
    if template is not None:
        template = str(template)

    content = raw.get('content')
    if content is not None:
        content = str(content)

    ref = raw.get('ref')
    if ref is not None:
        ref = str(ref).strip()
        if not ref:
            raise ValidationError(f'{manifest_path}: assets[{index}].ref must be a non-empty string')
        if not IDENTIFIER_PATTERN.fullmatch(ref):
            raise ValidationError(
                f'{manifest_path}: assets[{index}].ref must match {IDENTIFIER_PATTERN.pattern}'
            )

    return AssetSpec(
        type=asset_type,  # type: ignore[arg-type]
        path=path.strip(),
        template=template,
        content=content,
        ref=ref,
    )


def _parse_action_spec(raw: Any, manifest_path: Path, index: int) -> ActionSpec:
    if not isinstance(raw, dict):
        raise ValidationError(
            f'{manifest_path}: actions[{index}] must be an object, got {type(raw).__name__}'
        )

    phase = str(raw.get('phase', 'post')).strip()
    if phase not in VALID_ACTION_PHASES:
        raise ValidationError(
            f'{manifest_path}: actions[{index}].phase must be one of {sorted(VALID_ACTION_PHASES)}'
        )

    run_raw = raw.get('run')
    shell_raw = raw.get('shell')
    if (run_raw is None) == (shell_raw is None):
        raise ValidationError(
            f'{manifest_path}: actions[{index}] must define exactly one of run or shell'
        )

    run: list[str] | None = None
    if run_raw is not None:
        if not isinstance(run_raw, list) or not run_raw:
            raise ValidationError(f'{manifest_path}: actions[{index}].run must be a non-empty list')
        run = [str(item) for item in run_raw]
        if any(not part for part in run):
            raise ValidationError(f'{manifest_path}: actions[{index}].run items must not be empty')

    shell: str | None = None
    if shell_raw is not None:
        shell = str(shell_raw).strip()
        if not shell:
            raise ValidationError(f'{manifest_path}: actions[{index}].shell must be a non-empty string')

    cwd = raw.get('cwd')
    cwd_text = None if cwd is None else str(cwd).strip()
    if cwd_text == '':
        raise ValidationError(f'{manifest_path}: actions[{index}].cwd must not be empty')

    description = str(raw.get('description', ''))
    return ActionSpec(
        phase=phase,  # type: ignore[arg-type]
        run=run,
        shell=shell,
        cwd=cwd_text,
        description=description,
    )


def load_command_spec(package_dir: Path) -> CommandSpec:
    manifest_path = _manifest_path_for(package_dir)
    data = _load_mapping_file(manifest_path)

    name = str(data.get('name', package_dir.name)).strip()
    if not name:
        raise ValidationError(f'{manifest_path}: command name cannot be empty')

    description = str(data.get('description', '')).strip()

    conflict = data.get('conflict')
    conflict_policy: ConflictPolicy | None
    if conflict is None:
        conflict_policy = None
    else:
        conflict_text = str(conflict)
        if conflict_text not in VALID_CONFLICT_POLICIES:
            raise ValidationError(
                f'{manifest_path}: conflict must be one of {sorted(VALID_CONFLICT_POLICIES)}'
            )
        conflict_policy = conflict_text  # type: ignore[assignment]

    inputs_raw = data.get('inputs', [])
    if not isinstance(inputs_raw, list):
        raise ValidationError(f'{manifest_path}: inputs must be a list')
    inputs = [_parse_input_spec(item, manifest_path, i) for i, item in enumerate(inputs_raw)]

    seen_input_names: set[str] = set()
    for input_spec in inputs:
        if input_spec.name in seen_input_names:
            raise ValidationError(f"{manifest_path}: duplicate input name '{input_spec.name}'")
        seen_input_names.add(input_spec.name)

    assets_raw = data.get('assets', [])
    if not isinstance(assets_raw, list) or not assets_raw:
        raise ValidationError(f'{manifest_path}: assets must be a non-empty list')
    assets = [_parse_asset_spec(item, manifest_path, i) for i, item in enumerate(assets_raw)]

    seen_refs: set[str] = set()
    for i, asset in enumerate(assets):
        if asset.template:
            template_path = package_dir / asset.template
            if not template_path.exists() or not template_path.is_file():
                raise ValidationError(
                    f'{manifest_path}: assets[{i}].template not found: {asset.template}'
                )
        if asset.ref is not None:
            if asset.ref in seen_refs:
                raise ValidationError(f"{manifest_path}: duplicate asset ref '{asset.ref}'")
            seen_refs.add(asset.ref)

    actions_raw = data.get('actions', [])
    if not isinstance(actions_raw, list):
        raise ValidationError(f'{manifest_path}: actions must be a list')
    actions = [_parse_action_spec(item, manifest_path, i) for i, item in enumerate(actions_raw)]

    return CommandSpec(
        name=name,
        description=description,
        package_dir=package_dir,
        manifest_path=manifest_path,
        inputs=inputs,
        assets=assets,
        actions=actions,
        conflict=conflict_policy,
    )


def load_registry(start_dir: Path) -> CommandRegistry:
    root = discover_project_root(start_dir)
    sprout_dir = root / '.sprout'
    config = _read_project_config(sprout_dir)

    loaded: list[CommandSpec] = []
    invalid: list[CommandIssue] = []

    for child in iter_command_package_dirs(sprout_dir):
        try:
            loaded.append(load_command_spec(child))
        except ValidationError as exc:
            invalid.append(CommandIssue(name=child.name, source=child, message=str(exc)))

    grouped: dict[str, list[CommandSpec]] = {}
    for command in loaded:
        grouped.setdefault(command.name, []).append(command)

    commands: dict[str, CommandSpec] = {}
    conflicts: list[CommandIssue] = []

    for name, items in grouped.items():
        if len(items) == 1:
            commands[name] = items[0]
            continue

        sources = [str(item.package_dir) for item in items]
        for item in items:
            others = [src for src in sources if src != str(item.package_dir)]
            conflicts.append(
                CommandIssue(
                    name=name,
                    source=item.package_dir,
                    message=(
                        f"Duplicate command name '{name}'. Conflicts with: {', '.join(others)}"
                    ),
                )
            )

    return CommandRegistry(
        root=root,
        sprout_dir=sprout_dir,
        config=config,
        commands=commands,
        invalid=invalid,
        conflicts=conflicts,
    )


# ================================================
# Section: Input collection
# ================================================


def parse_key_value_pairs(items: list[str]) -> dict[str, str]:
    values: dict[str, str] = {}
    for item in items:
        if '=' not in item:
            if ':' in item:
                raise ValidationError(
                    f"Invalid input '{item}'. Use key=value format (with '=', not ':'), e.g. name=my-task"
                )
            raise ValidationError(
                f"Invalid input '{item}'. Use key=value format, e.g. name=my-task"
            )
        key, value = item.split('=', 1)
        key = key.strip()
        if not key:
            raise ValidationError(f"Invalid input '{item}': key cannot be empty")
        values[key] = value
    return values


def _validate_json_input_mapping(data: Any, *, source: str) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ValidationError(f'JSON input must be an object in {source}')

    values: dict[str, Any] = {}
    for key, value in data.items():
        if not isinstance(key, str) or not key.strip():
            raise ValidationError(f'JSON input keys must be non-empty strings in {source}')
        if isinstance(value, (dict, list)):
            raise ValidationError(
                f"JSON input '{key}' in {source} must be a string, number, boolean, or null"
            )
        values[key] = value
    return values


def parse_json_input(raw: str) -> dict[str, Any]:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValidationError(
            f'Invalid JSON input: {exc.msg} at line {exc.lineno} column {exc.colno}'
        ) from exc
    return _validate_json_input_mapping(data, source='--json')


def load_json_input_file(path: Path) -> dict[str, Any]:
    if not path.exists() or not path.is_file():
        raise ValidationError(f'JSON input file not found: {path}')

    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except json.JSONDecodeError as exc:
        raise ValidationError(
            f"Invalid JSON input file '{path}': {exc.msg} at line {exc.lineno} column {exc.colno}"
        ) from exc
    return _validate_json_input_mapping(data, source=str(path))


def merge_input_sources(base: dict[str, Any], overrides: dict[str, str]) -> dict[str, Any]:
    merged = dict(base)
    merged.update(overrides)
    return merged


def _coerce_number(spec: InputSpec, raw: Any) -> int | float:
    try:
        value = float(raw)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"Input '{spec.name}' must be a number") from exc

    if spec.minimum is not None and value < spec.minimum:
        raise ValidationError(f"Input '{spec.name}' must be >= {spec.minimum:g}, got {value:g}")
    if spec.maximum is not None and value > spec.maximum:
        raise ValidationError(f"Input '{spec.name}' must be <= {spec.maximum:g}, got {value:g}")

    if value.is_integer():
        return int(value)
    return value


def _coerce_input_value(spec: InputSpec, raw: Any) -> Any:
    if spec.type == 'string':
        return '' if raw is None else str(raw)
    if spec.type == 'number':
        return _coerce_number(spec, raw)
    if spec.type == 'enum':
        text = '' if raw is None else str(raw)
        if text not in spec.enum:
            raise ValidationError(f"Input '{spec.name}' must be one of {spec.enum}, got '{text}'")
        return text
    raise ValidationError(f'Unknown input type: {spec.type}')


def build_prompt_info(spec: InputSpec) -> PromptInfo:
    requirement = 'required' if spec.required else 'optional'
    detail_parts: list[str] = []

    if spec.type == 'enum':
        detail_parts.append(f"choices: {', '.join(spec.enum)}")
    elif spec.type == 'number':
        bounds: list[str] = []
        if spec.minimum is not None:
            bounds.append(f'min={spec.minimum:g}')
        if spec.maximum is not None:
            bounds.append(f'max={spec.maximum:g}')
        detail_parts.append('number' if not bounds else f"number ({', '.join(bounds)})")
    else:
        detail_parts.append('text')

    if spec.default is not None:
        detail_parts.append(f'default: {spec.default}')

    return PromptInfo(
        title=f'{spec.name} ({requirement})',
        description=spec.description or 'No description provided.',
        detail=' | '.join(detail_parts),
    )


def _read_prompt_value(prompt: Callable[[str], str] | None, message: str) -> str:
    reader = prompt or input
    try:
        raw = reader(message)
    except (EOFError, KeyboardInterrupt) as exc:
        raise UserAbortError('Cancelled. No files were created.') from exc

    if raw.strip().lower() in CANCEL_INPUTS:
        raise UserAbortError('Cancelled. No files were created.')
    return raw


def _prompt_missing_value(spec: InputSpec, prompt: Callable[[str], str] | None) -> Any:
    info = build_prompt_info(spec)
    message = f'{info.title}\n{info.description}\n{info.detail}\n> '

    while True:
        raw = _read_prompt_value(prompt, message).strip()

        if raw == '' and spec.default is not None:
            raw = str(spec.default)
        if raw == '' and not spec.required:
            return ''
        if raw == '' and spec.type == 'string' and spec.required:
            print(f"Invalid value: Input '{spec.name}' cannot be empty")
            continue

        try:
            return _coerce_input_value(spec, raw)
        except ValidationError as exc:
            print(f'Invalid value: {exc}')


def find_missing_required_inputs(
    command: CommandSpec,
    provided: dict[str, Any],
) -> list[InputSpec]:
    missing: list[InputSpec] = []
    for spec in command.inputs:
        if spec.name in provided:
            continue
        if spec.default is not None:
            continue
        if spec.required:
            missing.append(spec)
    return missing


def collect_inputs(
    command: CommandSpec,
    provided: dict[str, Any],
    *,
    interactive: bool,
    prompt: Callable[[str], str] | None = None,
) -> dict[str, Any]:
    known_names = {input_spec.name for input_spec in command.inputs}
    unknown = sorted(set(provided.keys()) - known_names)
    if unknown:
        raise ValidationError(f"Unknown inputs for command '{command.name}': {', '.join(unknown)}")

    values: dict[str, Any] = {}
    missing_required: list[str] = []

    for spec in command.inputs:
        if spec.name in provided:
            values[spec.name] = _coerce_input_value(spec, provided[spec.name])
            continue
        if spec.default is not None:
            values[spec.name] = _coerce_input_value(spec, spec.default)
            continue
        if interactive:
            values[spec.name] = _prompt_missing_value(spec, prompt)
            continue
        if spec.required:
            missing_required.append(spec.name)
        else:
            values[spec.name] = ''

    if missing_required:
        raise ValidationError('Missing required inputs: ' + ', '.join(sorted(missing_required)))
    return values


def suggest_command_names(name: str, available: list[str], *, limit: int = 3) -> list[str]:
    try:
        from difflib import get_close_matches
    except ImportError:
        return []
    return get_close_matches(name, available, n=limit, cutoff=0.5)


# ================================================
# Section: Template rendering and validation
# ================================================


def build_variable_context(values: dict[str, Any], now: datetime | None = None) -> dict[str, Any]:
    timestamp = now or datetime.now()
    context: dict[str, Any] = dict(values)
    context.update(
        {
            'YYYY': timestamp.strftime('%Y'),
            'YY': timestamp.strftime('%y'),
            'MM': timestamp.strftime('%m'),
            'DD': timestamp.strftime('%d'),
            'hh': timestamp.strftime('%H'),
            'mm': timestamp.strftime('%M'),
            'ss': timestamp.strftime('%S'),
            'date': timestamp.strftime('%Y-%m-%d'),
            'time': timestamp.strftime('%H:%M:%S'),
            'datetime': timestamp.strftime('%Y-%m-%dT%H:%M:%S'),
            'timestamp': str(int(timestamp.timestamp())),
        }
    )
    return context


def _list_placeholders(template: str) -> list[str]:
    return [match.group(1).strip() for match in PLACEHOLDER_PATTERN.finditer(template)]


def generate_random_token(kind: Literal['str', 'num'], length: int) -> str:
    if length <= 0 or length > MAX_RANDOM_LENGTH:
        raise ValidationError(
            f'Random token length must be between 1 and {MAX_RANDOM_LENGTH}, got {length}'
        )
    alphabet = string.digits if kind == 'num' else string.digits + string.ascii_letters
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def _build_project_context(project_root: Path) -> dict[str, str]:
    resolved_root = project_root.resolve()
    return {
        'project.root': resolved_root.as_posix(),
        'project.root_name': project_root.name,
    }


def _path_to_rel_string(project_root: Path, path: Path) -> str:
    return path.resolve(strict=False).relative_to(project_root.resolve()).as_posix()


def _build_asset_ref_entries(project_root: Path, ref: str, final_path: Path, *, include_bare_abs: bool) -> dict[str, str]:
    rel_path = _path_to_rel_string(project_root, final_path)
    abs_path = final_path.resolve(strict=False).as_posix()
    parent = final_path.parent.resolve(strict=False)
    parent_rel = parent.relative_to(project_root.resolve()).as_posix()
    if parent_rel == '.':
        parent_rel = ''

    entries = {
        f'assets.{ref}.abs_path': abs_path,
        f'assets.{ref}.rel_path': rel_path,
        f'assets.{ref}.name': final_path.name,
        f'assets.{ref}.parent_abs': parent.as_posix(),
        f'assets.{ref}.parent_rel': parent_rel,
    }
    if include_bare_abs:
        entries[f'assets.{ref}'] = abs_path
    return entries


def _build_asset_ref_context(
    project_root: Path,
    ref_paths: dict[str, Path],
    *,
    include_bare_abs: bool,
) -> dict[str, str]:
    context: dict[str, str] = {}
    for ref, final_path in ref_paths.items():
        context.update(
            _build_asset_ref_entries(project_root, ref, final_path, include_bare_abs=include_bare_abs)
        )
    return context


def _asset_context_keys(ref_names: set[str], *, include_bare_abs: bool) -> set[str]:
    keys: set[str] = set()
    for ref in ref_names:
        if include_bare_abs:
            keys.add(f'assets.{ref}')
        for suffix in sorted(VALID_ASSET_SUFFIXES):
            keys.add(f'assets.{ref}.{suffix}')
    return keys


def _missing_expression_error(expression: str, *, scope: Literal['base', 'asset', 'action']) -> ValidationError:
    asset_match = re.fullmatch(r'assets\.([A-Za-z_][A-Za-z0-9_]*)(?:\.([A-Za-z_][A-Za-z0-9_]*))?$', expression)
    if asset_match:
        suffix = asset_match.group(2)
        if suffix is None and scope == 'asset':
            return ValidationError(
                f"Bare asset reference '{{{{{expression}}}}}' is not allowed here. Use an explicit suffix such as '.rel_path'."
            )
        if suffix is not None and suffix not in VALID_ASSET_SUFFIXES:
            return ValidationError(
                f"Unsupported asset suffix in '{{{{{expression}}}}}'. Use one of {sorted(VALID_ASSET_SUFFIXES)}."
            )
        if scope == 'base':
            return ValidationError(f"Asset references are not available in '{{{{{expression}}}}}'.")
        return ValidationError(
            f"Unknown asset reference or forward reference '{{{{{expression}}}}}'."
        )

    if expression.startswith('rand.'):
        return ValidationError(
            f"Invalid random token '{{{{{expression}}}}}'. Use rand.str[:N] or rand.num[:N]."
        )

    return ValidationError(f"Missing variable '{expression}' for template rendering")


def _resolve_expression(
    expression: str,
    context: dict[str, Any],
    *,
    scope: Literal['base', 'asset', 'action'],
) -> str:
    rand_match = RAND_EXPR_PATTERN.fullmatch(expression)
    if rand_match:
        kind = rand_match.group(1)
        length = int(rand_match.group(2) or DEFAULT_RANDOM_LENGTH)
        return generate_random_token(kind, length)  # type: ignore[arg-type]

    if expression in context:
        value = context[expression]
        return '' if value is None else str(value)

    raise _missing_expression_error(expression, scope=scope)


def render_text(
    template: str,
    context: dict[str, Any],
    *,
    scope: Literal['base', 'asset', 'action'] = 'base',
) -> str:
    def replace(match: re.Match[str]) -> str:
        expression = match.group(1).strip()
        return _resolve_expression(expression, context, scope=scope)

    return PLACEHOLDER_PATTERN.sub(replace, template)


def _validate_template_text(
    text: str,
    *,
    template_name: str,
    command_name: str,
    scope: Literal['asset', 'action'],
    allowed_keys: set[str],
) -> list[TemplateValidationIssue]:
    issues: list[TemplateValidationIssue] = []
    dummy_context = {key: 'x' for key in allowed_keys}

    for expression in _list_placeholders(text):
        try:
            _resolve_expression(expression, dummy_context, scope=scope)
        except ValidationError as exc:
            issues.append(
                TemplateValidationIssue(
                    command_name=command_name,
                    template_path=template_name,
                    undefined_variables=[expression],
                    message=str(exc),
                )
            )
    return issues


def validate_template_variables(command: CommandSpec) -> list[TemplateValidationIssue]:
    issues: list[TemplateValidationIssue] = []
    base_keys = {input_spec.name for input_spec in command.inputs}
    base_keys.update(BUILTIN_VARIABLES)
    base_keys.update(PROJECT_VARIABLES)

    seen_refs: set[str] = set()
    for index, asset in enumerate(command.assets):
        asset_keys = set(base_keys)
        asset_keys.update(_asset_context_keys(seen_refs, include_bare_abs=False))
        issues.extend(
            _validate_template_text(
                asset.path,
                template_name=f'assets[{index}].path',
                command_name=command.name,
                scope='asset',
                allowed_keys=asset_keys,
            )
        )

        template_name = asset.template or '<inline>'
        template_content = ''
        if asset.template:
            template_path = command.package_dir / asset.template
            if template_path.exists():
                template_content = template_path.read_text(encoding='utf-8')
        elif asset.content:
            template_content = asset.content

        if template_content:
            issues.extend(
                _validate_template_text(
                    template_content,
                    template_name=template_name,
                    command_name=command.name,
                    scope='asset',
                    allowed_keys=asset_keys,
                )
            )

        if asset.ref is not None:
            seen_refs.add(asset.ref)

    action_keys = set(base_keys)
    action_keys.update(_asset_context_keys(seen_refs, include_bare_abs=True))
    for index, action in enumerate(command.actions):
        if action.cwd:
            issues.extend(
                _validate_template_text(
                    action.cwd,
                    template_name=f'actions[{index}].cwd',
                    command_name=command.name,
                    scope='action',
                    allowed_keys=action_keys,
                )
            )
        if action.shell:
            issues.extend(
                _validate_template_text(
                    action.shell,
                    template_name=f'actions[{index}].shell',
                    command_name=command.name,
                    scope='action',
                    allowed_keys=action_keys,
                )
            )
        if action.run:
            for arg_index, part in enumerate(action.run):
                issues.extend(
                    _validate_template_text(
                        part,
                        template_name=f'actions[{index}].run[{arg_index}]',
                        command_name=command.name,
                        scope='action',
                        allowed_keys=action_keys,
                    )
                )

    return issues


# ================================================
# Section: Generation planning and application
# ================================================


def _ensure_within_root(root: Path, target: Path) -> None:
    root_resolved = root.resolve()
    target_resolved = target.resolve(strict=False)
    if target_resolved == root_resolved:
        return
    if root_resolved not in target_resolved.parents:
        raise ValidationError(f'Rendered path escapes project root: {target}')


def _rename_with_suffix(path: Path, occupied: set[Path]) -> Path:
    suffix = path.suffix
    stem = path.stem if suffix else path.name
    parent = path.parent

    index = 2
    while True:
        candidate = parent / (f'{stem}_{index:02d}{suffix}' if suffix else f'{stem}_{index:02d}')
        if not candidate.exists() and candidate not in occupied:
            return candidate
        index += 1


def _resolve_asset_action(
    target: Path,
    asset: AssetSpec,
    policy: ConflictPolicy,
    occupied: set[Path],
) -> tuple[str, Path]:
    path_exists = target.exists()
    already_planned = target in occupied

    if already_planned:
        raise GenerationError(f'Duplicate rendered target path in one run: {target}')

    if not path_exists:
        return 'create', target
    if asset.type == 'file' and target.is_dir():
        raise GenerationError(f'Target exists as directory but file asset requested: {target}')
    if asset.type == 'dir' and target.is_file():
        raise GenerationError(f'Target exists as file but directory asset requested: {target}')
    if asset.type == 'dir':
        return 'reuse', target
    if policy == 'fail':
        raise GenerationError(
            f'Target already exists: {target}\n'
            'Hint: Use --conflict=skip to skip existing files, or --conflict=overwrite to replace them.'
        )
    if policy == 'skip':
        return 'skip', target
    if policy == 'overwrite':
        return 'overwrite', target
    if policy == 'rename':
        return 'rename', _rename_with_suffix(target, occupied)
    raise GenerationError(f'Unsupported conflict policy: {policy}')


def effective_conflict_policy(
    command: CommandSpec,
    project_config: ProjectConfig,
    override: str | None,
) -> ConflictPolicy:
    if override is not None:
        if override not in VALID_CONFLICT_POLICIES:
            raise ValidationError(
                f'Conflict policy must be one of {sorted(VALID_CONFLICT_POLICIES)}'
            )
        return override  # type: ignore[return-value]
    if command.conflict is not None:
        return command.conflict
    if project_config.conflict in VALID_CONFLICT_POLICIES:
        return project_config.conflict
    return 'fail'


def build_generation_plan(
    command: CommandSpec,
    project_root: Path,
    context: dict[str, Any],
    policy: ConflictPolicy,
) -> list[PlannedAsset]:
    occupied: set[Path] = set()
    planned: list[PlannedAsset] = []
    ref_paths: dict[str, Path] = {}

    for index, asset in enumerate(command.assets):
        asset_context = dict(context)
        asset_context.update(_build_project_context(project_root))
        asset_context.update(
            _build_asset_ref_context(project_root, ref_paths, include_bare_abs=False)
        )

        requested_path = render_text(asset.path, asset_context, scope='asset').strip()
        if not requested_path:
            raise ValidationError(
                f"Command '{command.name}' rendered empty target path for asset #{index + 1}"
            )

        relative_path = Path(requested_path)
        if relative_path.is_absolute():
            raise ValidationError(
                f"Command '{command.name}' rendered an absolute path: {requested_path}"
            )

        target = (project_root / relative_path).resolve(strict=False)
        _ensure_within_root(project_root, target)

        content: str | None = None
        if asset.type == 'file':
            if asset.template is not None:
                template_path = command.package_dir / asset.template
                template_text = template_path.read_text(encoding='utf-8')
                content = render_text(template_text, asset_context, scope='asset')
            elif asset.content is not None:
                content = render_text(asset.content, asset_context, scope='asset')
            else:
                content = ''

        action, final_path = _resolve_asset_action(target, asset, policy, occupied)
        if final_path in occupied:
            raise GenerationError(f'Duplicate rendered target path in one run: {final_path}')
        if action != 'skip':
            occupied.add(final_path)

        planned_item = PlannedAsset(
            index=index,
            asset=asset,
            requested_path=requested_path.replace('\\', '/'),
            target_path=target,
            final_path=final_path,
            action=action,
            content=content,
        )
        planned.append(planned_item)

        if asset.ref is not None:
            ref_paths[asset.ref] = final_path

    return sorted(planned, key=lambda item: (0 if item.asset.type == 'dir' else 1, item.index))


def apply_generation_plan(
    plan: list[PlannedAsset],
    project_root: Path,
    *,
    dry_run: bool = False,
) -> list[GeneratedItem]:
    del project_root

    results: list[GeneratedItem] = []
    for item in plan:
        if item.action == 'skip':
            results.append(
                GeneratedItem(
                    asset_type=item.asset.type,
                    requested_path=item.requested_path,
                    final_path=item.final_path,
                    action='skip',
                    ref=item.asset.ref,
                )
            )
            continue

        if not dry_run:
            if item.asset.type == 'dir':
                item.final_path.mkdir(parents=True, exist_ok=True)
            else:
                item.final_path.parent.mkdir(parents=True, exist_ok=True)
                item.final_path.write_text(item.content or '', encoding='utf-8')

        results.append(
            GeneratedItem(
                asset_type=item.asset.type,
                requested_path=item.requested_path,
                final_path=item.final_path,
                action=item.action,  # type: ignore[arg-type]
                ref=item.asset.ref,
            )
        )

    return results


# ================================================
# Section: Action planning and execution
# ================================================


def build_action_context(
    values: dict[str, Any],
    generated: list[GeneratedItem],
    project_root: Path,
) -> dict[str, Any]:
    context = dict(values)
    context.update(_build_project_context(project_root))
    ref_paths = {item.ref: item.final_path for item in generated if item.ref is not None}
    context.update(_build_asset_ref_context(project_root, ref_paths, include_bare_abs=True))
    return context


def _resolve_action_cwd(cwd_text: str, project_root: Path) -> Path:
    cwd_path = Path(cwd_text)
    if not cwd_path.is_absolute():
        cwd_path = (project_root / cwd_path).resolve(strict=False)
    else:
        cwd_path = cwd_path.resolve(strict=False)
    _ensure_within_root(project_root, cwd_path)
    return cwd_path


def _format_command_display(argv: list[str] | None = None, shell: str | None = None) -> str:
    if argv is not None:
        return subprocess.list2cmdline(argv)
    return shell or ''


def plan_post_actions(
    command: CommandSpec,
    project_root: Path,
    values: dict[str, Any],
    generated: list[GeneratedItem],
) -> list[PlannedAction]:
    context = build_action_context(values, generated, project_root)
    planned: list[PlannedAction] = []

    for index, action in enumerate(command.actions):
        cwd = None
        if action.cwd is not None:
            rendered_cwd = render_text(action.cwd, context, scope='action').strip()
            if not rendered_cwd:
                raise ValidationError(f"Command '{command.name}' rendered empty cwd for action #{index + 1}")
            cwd = _resolve_action_cwd(rendered_cwd, project_root)

        if action.run is not None:
            argv = [render_text(part, context, scope='action') for part in action.run]
            planned.append(
                PlannedAction(
                    index=index,
                    mode='argv',
                    command_display=_format_command_display(argv=argv),
                    cwd=cwd,
                    argv=argv,
                )
            )
            continue

        if action.shell is None:
            raise ValidationError(f"Command '{command.name}' action #{index + 1} has no executable")

        shell_command = render_text(action.shell, context, scope='action')
        planned.append(
            PlannedAction(
                index=index,
                mode='shell',
                command_display=_format_command_display(shell=shell_command),
                cwd=cwd,
                shell_command=shell_command,
            )
        )

    return planned


def execute_actions(actions: list[PlannedAction], *, dry_run: bool = False) -> None:
    for action in actions:
        if dry_run:
            continue

        try:
            if action.mode == 'argv':
                assert action.argv is not None
                completed = subprocess.run(action.argv, cwd=action.cwd, check=False)
            else:
                assert action.shell_command is not None
                completed = subprocess.run(action.shell_command, cwd=action.cwd, shell=True, check=False)
        except OSError as exc:
            raise GenerationError(
                f'Action #{action.index + 1} could not start: {action.command_display} ({exc})'
            ) from exc

        if completed.returncode != 0:
            raise GenerationError(
                f'Action #{action.index + 1} failed with exit code {completed.returncode}: '
                f'{action.command_display}'
            )
