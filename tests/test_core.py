from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from sprout.core import (
    build_prompt_info,
    build_variable_context,
    collect_inputs,
    discover_global_dir,
    discover_project_root,
    find_missing_required_inputs,
    iter_command_package_dirs,
    iter_global_command_package_dirs,
    load_command_spec,
    load_global_registry,
    load_json_input_file,
    load_registry,
    merge_input_sources,
    parse_json_input,
    validate_template_variables,
)
from sprout.models import DiscoveryError, UserAbortError, ValidationError


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
    def test_project_config_prefers_yaml_then_json_and_ignores_toml(self) -> None:
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
            self.assertEqual(registry.config.conflict, "fail")

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

    def test_registry_reads_preferred_and_legacy_command_dirs(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            preferred = root / '.sprout' / '__new__'
            legacy = root / '.sprout' / 'commands'

            _write(preferred / 'issue' / 'manifest.json', _manifest('issue'))
            _write(preferred / 'issue' / 'template.md', '# {{name}}')
            _write(legacy / 'task' / 'manifest.json', _manifest('task'))
            _write(legacy / 'task' / 'template.md', '# {{name}}')

            package_dirs = iter_command_package_dirs(root / '.sprout')
            self.assertEqual([path.name for path in package_dirs], ['issue', 'task'])

            registry = load_registry(root)
            self.assertEqual(sorted(registry.commands.keys()), ['issue', 'task'])

    def test_registry_marks_conflict_and_keeps_invalid_isolated(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            preferred = root / '.sprout' / '__new__'
            legacy = root / '.sprout' / 'commands'

            # valid package A
            _write(preferred / 'alpha' / 'manifest.json', _manifest('dup'))
            _write(preferred / 'alpha' / 'template.md', '# {{name}}')

            # valid package B with same command name -> conflict across dirs
            _write(legacy / 'beta' / 'manifest.json', _manifest('dup'))
            _write(legacy / 'beta' / 'template.md', '# {{name}}')

            # invalid package should not break others
            _write(legacy / 'broken' / 'manifest.json', json.dumps({'name': 'broken'}))

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

    def test_validate_template_variables_supports_actions_and_refs(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            command_dir = root / '.sprout' / 'commands' / 'demo'
            _write(
                command_dir / 'manifest.json',
                json.dumps(
                    {
                        'name': 'demo',
                        'inputs': [{'name': 'name', 'type': 'string'}],
                        'assets': [
                            {'type': 'dir', 'path': 'projects/{{name}}', 'ref': 'project_dir'},
                            {'type': 'file', 'path': '{{assets.project_dir.rel_path}}/README.md', 'content': 'x'},
                        ],
                        'actions': [
                            {'phase': 'post', 'shell': 'echo {{assets.project_dir}}', 'cwd': '{{assets.project_dir}}'},
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
            )
            command = load_command_spec(command_dir)
            issues = validate_template_variables(command)
            self.assertEqual(issues, [])


class GlobalModeTests(unittest.TestCase):
    def test_discover_global_dir_raises_when_missing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            import sprout.core as core
            original = core.GLOBAL_SPROUT_DIR
            core.GLOBAL_SPROUT_DIR = Path(td) / 'nonexistent'
            try:
                with self.assertRaises(DiscoveryError):
                    discover_global_dir()
            finally:
                core.GLOBAL_SPROUT_DIR = original

    def test_discover_global_dir_succeeds_when_present(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            import sprout.core as core
            original = core.GLOBAL_SPROUT_DIR
            global_dir = Path(td) / 'sprout'
            global_dir.mkdir()
            (global_dir / '__new__').mkdir()
            core.GLOBAL_SPROUT_DIR = global_dir
            try:
                result = discover_global_dir()
                self.assertEqual(result, global_dir)
            finally:
                core.GLOBAL_SPROUT_DIR = original

    def test_iter_global_command_package_dirs_only_scans_new(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            global_dir = Path(td) / 'sprout'
            new_dir = global_dir / '__new__'
            new_dir.mkdir(parents=True)

            # Only __new__/ should be scanned, not commands/
            cmd_dir = new_dir / 'mycmd'
            cmd_dir.mkdir()
            _write(cmd_dir / 'manifest.json', _manifest('mycmd'))

            result = iter_global_command_package_dirs(global_dir)
            self.assertEqual([p.name for p in result], ['mycmd'])

    def test_load_global_registry(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            import sprout.core as core
            original = core.GLOBAL_SPROUT_DIR
            global_dir = Path(td) / 'sprout'
            new_dir = global_dir / '__new__'
            cmd = new_dir / 'greeter'
            cmd.mkdir(parents=True)
            _write(cmd / 'manifest.json', _manifest('greeter'))
            _write(cmd / 'template.md', '# {{name}}')
            _write(global_dir / 'config.yaml', 'conflict: skip\n')
            core.GLOBAL_SPROUT_DIR = global_dir
            try:
                registry = load_global_registry()
                self.assertTrue(registry.is_global)
                self.assertIn('greeter', registry.commands)
                self.assertEqual(registry.config.conflict, 'skip')
            finally:
                core.GLOBAL_SPROUT_DIR = original

    def test_build_variable_context_global_mode(self) -> None:
        context = build_variable_context({'name': 'test'}, mode='global')
        self.assertIn('home', context)
        self.assertIn('cwd', context)
        self.assertIn('platform', context)
        self.assertNotIn('project.root', context)
        self.assertNotIn('project.root_name', context)

    def test_build_variable_context_project_mode_no_project_root(self) -> None:
        context = build_variable_context({'name': 'test'}, mode='project')
        self.assertNotIn('home', context)
        self.assertNotIn('cwd', context)
        self.assertNotIn('project.root', context)

    def test_build_variable_context_project_mode_with_project_root(self) -> None:
        project_root = Path('/tmp/myproject')
        context = build_variable_context({'name': 'test'}, mode='project', project_root=project_root)
        self.assertIn('project.root', context)
        self.assertIn('project.root_name', context)
        self.assertEqual(context['project.root_name'], 'myproject')
        self.assertNotIn('home', context)

    def test_command_spec_root_field(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            command_dir = Path(td) / 'cmd'
            command_dir.mkdir()
            _write(
                command_dir / 'manifest.json',
                json.dumps({
                    'name': 'temp',
                    'root': '{{home}}/temp',
                    'inputs': [{'name': 'name', 'type': 'string'}],
                    'assets': [{'type': 'dir', 'path': '{{name}}'}],
                }),
            )
            command = load_command_spec(command_dir)
            self.assertEqual(command.root, '{{home}}/temp')

    def test_command_spec_no_root(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            command_dir = Path(td) / 'cmd'
            command_dir.mkdir()
            _write(
                command_dir / 'manifest.json',
                json.dumps({
                    'name': 'issue',
                    'inputs': [{'name': 'name', 'type': 'string'}],
                    'assets': [{'type': 'dir', 'path': 'issues'}],
                }),
            )
            command = load_command_spec(command_dir)
            self.assertIsNone(command.root)

    def test_validate_template_variables_global_mode(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            command_dir = Path(td) / 'cmd'
            command_dir.mkdir()
            _write(
                command_dir / 'manifest.json',
                json.dumps({
                    'name': 'temp',
                    'root': '{{home}}/temp',
                    'inputs': [{'name': 'name', 'type': 'string'}],
                    'assets': [{'type': 'dir', 'path': '{{name}}'}],
                }),
            )
            command = load_command_spec(command_dir)
            # Global mode: home/cwd/platform are valid in asset path
            issues = validate_template_variables(command, is_global=True)
            self.assertEqual(issues, [])

            # Global mode: project.* should not be available
            proj_cmd_dir = Path(td) / 'cmd2'
            proj_cmd_dir.mkdir()
            _write(
                proj_cmd_dir / 'manifest.json',
                json.dumps({
                    'name': 'proj',
                    'inputs': [],
                    'assets': [{'type': 'dir', 'path': '{{project.root}}/stuff'}],
                }),
            )
            proj_command = load_command_spec(proj_cmd_dir)
            issues_bad = validate_template_variables(proj_command, is_global=True)
            self.assertGreater(len(issues_bad), 0)

            # Project mode: home/cwd/platform should be flagged
            home_cmd_dir = Path(td) / 'cmd3'
            home_cmd_dir.mkdir()
            _write(
                home_cmd_dir / 'manifest.json',
                json.dumps({
                    'name': 'homecmd',
                    'inputs': [],
                    'assets': [{'type': 'dir', 'path': '{{home}}/mystuff'}],
                }),
            )
            home_command = load_command_spec(home_cmd_dir)
            home_issues = validate_template_variables(home_command, is_global=False)
            self.assertGreater(len(home_issues), 0)
