from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from sprout.core import (
    build_prompt_info,
    build_variable_context,
    collect_inputs,
    discover_project_root,
    find_missing_required_inputs,
    load_command_spec,
    load_json_input_file,
    load_registry,
    merge_input_sources,
    parse_json_input,
)
from sprout.models import UserAbortError, ValidationError


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _manifest(name: str, *, number_with_bounds: bool = False) -> str:
    input_block = [
        {"name": "name", "type": "string"},
        {"name": "type", "type": "enum", "enum": ["bug", "feat"]},
    ]
    if number_with_bounds:
        input_block.append({"name": "priority", "type": "number", "min": 1, "max": 3})

    data = {
        "name": name,
        "inputs": input_block,
        "assets": [
            {"type": "dir", "path": "issues"},
            {
                "type": "file",
                "path": "issues/{{name}}.md",
                "template": "template.md",
            },
        ],
    }
    return json.dumps(data, ensure_ascii=False, indent=2)


class CoreTests(unittest.TestCase):
    def test_project_config_prefers_yaml_and_keeps_legacy_formats(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            commands = root / ".sprout" / "commands"
            _write(commands / "issue" / "manifest.yaml", _manifest("issue"))
            _write(commands / "issue" / "template.md", "# {{name}}")

            sprout_dir = root / ".sprout"
            _write(sprout_dir / "config.json", json.dumps({"conflict": "skip"}))
            _write(sprout_dir / "config.toml", 'conflict = "overwrite"\n')
            _write(sprout_dir / "config.yaml", "conflict: rename\n")

            registry = load_registry(root)
            self.assertEqual(registry.config.conflict, "rename")

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            commands = root / ".sprout" / "commands"
            _write(commands / "issue" / "manifest.json", _manifest("issue"))
            _write(commands / "issue" / "template.md", "# {{name}}")
            _write(root / ".sprout" / "config.toml", 'conflict = "overwrite"\n')

            registry = load_registry(root)
            self.assertEqual(registry.config.conflict, "overwrite")

    def test_invalid_yaml_project_config_reports_path(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            commands = root / ".sprout" / "commands"
            _write(commands / "issue" / "manifest.json", _manifest("issue"))
            _write(commands / "issue" / "template.md", "# {{name}}")
            _write(root / ".sprout" / "config.yaml", "conflict: maybe\n")

            with self.assertRaises(ValidationError) as ctx:
                load_registry(root)

            self.assertIn("config.yaml", str(ctx.exception))
            self.assertIn("conflict must be one of", str(ctx.exception))

    def test_discover_project_root_from_nested_directory(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / ".sprout").mkdir()
            nested = root / "a" / "b" / "c"
            nested.mkdir(parents=True)

            discovered = discover_project_root(nested)
            self.assertEqual(discovered, root)

    def test_registry_marks_conflict_and_keeps_invalid_isolated(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            commands = root / ".sprout" / "commands"

            # valid package A
            _write(commands / "alpha" / "manifest.json", _manifest("dup"))
            _write(commands / "alpha" / "template.md", "# {{name}}")

            # valid package B with same command name -> conflict
            _write(commands / "beta" / "manifest.json", _manifest("dup"))
            _write(commands / "beta" / "template.md", "# {{name}}")

            # invalid package should not break others
            _write(commands / "broken" / "manifest.json", json.dumps({"name": "broken"}))

            registry = load_registry(root)
            self.assertEqual(registry.commands, {})
            self.assertGreaterEqual(len(registry.conflicts), 2)
            self.assertEqual(len(registry.invalid), 1)

    def test_number_min_max_validation(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            command_dir = root / ".sprout" / "commands" / "issue"
            _write(command_dir / "manifest.json", _manifest("issue", number_with_bounds=True))
            _write(command_dir / "template.md", "# {{name}}")

            command = load_command_spec(command_dir)

            with self.assertRaises(ValidationError):
                collect_inputs(
                    command,
                    {"name": "x", "type": "bug", "priority": "0"},
                    interactive=False,
                )

            values = collect_inputs(
                command,
                {"name": "x", "type": "bug", "priority": "2"},
                interactive=False,
            )
            context = build_variable_context(values)
            self.assertEqual(context["priority"], 2)

    def test_parse_json_input_accepts_object_only(self) -> None:
        parsed = parse_json_input('{"name": "demo", "priority": 2}')
        self.assertEqual(parsed['name'], 'demo')
        self.assertEqual(parsed['priority'], 2)

        with self.assertRaises(ValidationError):
            parse_json_input('[1, 2, 3]')

        with self.assertRaises(ValidationError):
            parse_json_input('{"meta": {"nested": true}}')

    def test_load_json_input_file_and_merge_sources(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            json_path = root / 'inputs.json'
            json_path.write_text('{"name": "json-name", "type": "bug"}', encoding='utf-8')

            loaded = load_json_input_file(json_path)
            merged = merge_input_sources(loaded, {'name': 'override'})
            self.assertEqual(merged['name'], 'override')
            self.assertEqual(merged['type'], 'bug')

    def test_find_missing_required_inputs_and_prompt_info(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            command_dir = root / '.sprout' / 'commands' / 'issue'
            _write(command_dir / 'manifest.json', _manifest('issue'))
            _write(command_dir / 'template.md', '# {{name}}')

            command = load_command_spec(command_dir)
            missing = find_missing_required_inputs(command, {'type': 'bug'})
            self.assertEqual([spec.name for spec in missing], ['name'])

            prompt_info = build_prompt_info(command.inputs[1])
            self.assertIn('choices:', prompt_info.detail)

    def test_collect_inputs_interactive_cancel_and_required_empty_string(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            command_dir = root / '.sprout' / 'commands' / 'issue'
            _write(command_dir / 'manifest.json', _manifest('issue'))
            _write(command_dir / 'template.md', '# {{name}}')

            command = load_command_spec(command_dir)

            answers = iter(['', 'valid-name'])
            values = collect_inputs(
                command,
                {'type': 'bug'},
                interactive=True,
                prompt=lambda _: next(answers),
            )
            self.assertEqual(values['name'], 'valid-name')

            with self.assertRaises(UserAbortError):
                collect_inputs(
                    command,
                    {'type': 'bug'},
                    interactive=True,
                    prompt=lambda _: 'q',
                )


if __name__ == "__main__":
    unittest.main()
