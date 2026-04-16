from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from sprout.core import (
    apply_generation_plan,
    build_generation_plan,
    build_variable_context,
    execute_actions,
    load_command_spec,
    plan_post_actions,
    validate_template_variables,
)
from sprout.models import GenerationError, ValidationError


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')


class ActionTests(unittest.TestCase):
    def test_asset_backward_ref_and_random_tokens(self) -> None:
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
                            {
                                'type': 'file',
                                'path': '{{assets.project_dir.rel_path}}/__init__.py',
                                'content': 'token={{rand.str:6}}',
                                'ref': 'init_file',
                            },
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
            )
            command = load_command_spec(command_dir)
            context = build_variable_context({'name': 'sample'})

            plan = build_generation_plan(command, root, context, 'fail')
            self.assertEqual(plan[1].requested_path, 'projects/sample/__init__.py')
            self.assertRegex(plan[1].content or '', r'^token=[0-9A-Za-z]{6}$')

    def test_bare_asset_reference_disallowed_in_asset_path(self) -> None:
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
                            {'type': 'file', 'path': '{{assets.project_dir}}/README.md', 'content': ''},
                        ],
                    }
                ),
            )
            command = load_command_spec(command_dir)
            issues = validate_template_variables(command)
            self.assertTrue(any('Bare asset reference' in issue.message for issue in issues))

            with self.assertRaises(ValidationError):
                build_generation_plan(command, root, build_variable_context({'name': 'x'}), 'fail')

    def test_action_uses_abs_path_and_dry_run_does_not_execute(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            command_dir = root / '.sprout' / 'commands' / 'demo'
            output_file = root / 'action.txt'
            _write(
                command_dir / 'manifest.json',
                json.dumps(
                    {
                        'name': 'demo',
                        'inputs': [{'name': 'name', 'type': 'string'}],
                        'assets': [
                            {'type': 'dir', 'path': 'projects/{{name}}', 'ref': 'project_dir'},
                        ],
                        'actions': [
                            {
                                'phase': 'post',
                                'run': ['python', '-c', f"from pathlib import Path; Path(r'{output_file.as_posix()}').write_text('ok', encoding='utf-8')"],
                                'cwd': '{{assets.project_dir}}',
                            }
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
            )
            command = load_command_spec(command_dir)
            values = build_variable_context({'name': 'sample'})
            generated = apply_generation_plan(build_generation_plan(command, root, values, 'fail'), root)
            planned_actions = plan_post_actions(command, root, values, generated)

            self.assertTrue(planned_actions[0].cwd is not None and planned_actions[0].cwd.is_absolute())
            execute_actions(planned_actions, dry_run=True)
            self.assertFalse(output_file.exists())

            execute_actions(planned_actions, dry_run=False)
            self.assertEqual(output_file.read_text(encoding='utf-8'), 'ok')

    def test_action_failure_stops_execution(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            command_dir = root / '.sprout' / 'commands' / 'demo'
            _write(
                command_dir / 'manifest.json',
                json.dumps(
                    {
                        'name': 'demo',
                        'inputs': [{'name': 'name', 'type': 'string'}],
                        'assets': [{'type': 'dir', 'path': 'projects/{{name}}', 'ref': 'project_dir'}],
                        'actions': [
                            {'phase': 'post', 'run': ['python', '-c', 'import sys; sys.exit(7)']},
                        ],
                    }
                ),
            )
            command = load_command_spec(command_dir)
            values = build_variable_context({'name': 'sample'})
            generated = apply_generation_plan(build_generation_plan(command, root, values, 'fail'), root)
            planned_actions = plan_post_actions(command, root, values, generated)

            with self.assertRaises(GenerationError) as ctx:
                execute_actions(planned_actions)
            self.assertIn('Action #1 failed', str(ctx.exception))

    def test_action_missing_executable_is_wrapped_as_generation_error(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            command_dir = root / '.sprout' / 'commands' / 'demo'
            _write(
                command_dir / 'manifest.json',
                json.dumps(
                    {
                        'name': 'demo',
                        'inputs': [{'name': 'name', 'type': 'string'}],
                        'assets': [{'type': 'dir', 'path': 'projects/{{name}}', 'ref': 'project_dir'}],
                        'actions': [
                            {'phase': 'post', 'run': ['__sprout_missing_executable__']},
                        ],
                    }
                ),
            )
            command = load_command_spec(command_dir)
            values = build_variable_context({'name': 'sample'})
            generated = apply_generation_plan(build_generation_plan(command, root, values, 'fail'), root)
            planned_actions = plan_post_actions(command, root, values, generated)

            with self.assertRaises(GenerationError) as ctx:
                execute_actions(planned_actions)
            self.assertIn('could not start', str(ctx.exception))

    def test_action_invalid_cwd_is_wrapped_as_generation_error(self) -> None:
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
                            {'type': 'file', 'path': 'projects/{{name}}.txt', 'content': 'x', 'ref': 'project_file'},
                        ],
                        'actions': [
                            {'phase': 'post', 'run': ['python', '-c', 'print(1)'], 'cwd': '{{assets.project_file}}'},
                        ],
                    }
                ),
            )
            command = load_command_spec(command_dir)
            values = build_variable_context({'name': 'sample'})
            generated = apply_generation_plan(build_generation_plan(command, root, values, 'fail'), root)
            planned_actions = plan_post_actions(command, root, values, generated)

            with self.assertRaises(GenerationError) as ctx:
                execute_actions(planned_actions)
            self.assertIn('could not start', str(ctx.exception))

    def test_asset_ref_uses_final_renamed_path(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            command_dir = root / '.sprout' / 'commands' / 'demo'
            _write(root / 'issues' / 'sample.md', 'old')
            _write(
                command_dir / 'manifest.json',
                json.dumps(
                    {
                        'name': 'demo',
                        'inputs': [{'name': 'name', 'type': 'string'}],
                        'assets': [
                            {'type': 'file', 'path': 'issues/{{name}}.md', 'content': 'new', 'ref': 'note'},
                            {'type': 'file', 'path': '{{assets.note.rel_path}}.bak', 'content': 'backup'},
                        ],
                    }
                ),
            )
            command = load_command_spec(command_dir)
            values = build_variable_context({'name': 'sample'})
            plan = build_generation_plan(command, root, values, 'rename')
            apply_generation_plan(plan, root)

            self.assertTrue((root / 'issues' / 'sample_02.md').exists())
            self.assertTrue((root / 'issues' / 'sample_02.md.bak').exists())

    def test_global_action_context_supports_absolute_asset_refs(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            command_dir = root / '.sprout' / 'commands' / 'demo'
            outside = Path(td) / 'outside'
            _write(
                command_dir / 'manifest.json',
                json.dumps(
                    {
                        'name': 'demo',
                        'assets': [
                            {'type': 'file', 'path': str((outside / 'note.txt').resolve()), 'content': 'x', 'ref': 'note'},
                        ],
                        'actions': [
                            {'phase': 'post', 'shell': 'echo {{assets.note}} {{assets.note.rel_path}} {{assets.note.parent_rel}}'},
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
            )
            command = load_command_spec(command_dir)
            values = build_variable_context({}, mode='global')
            generated = apply_generation_plan(
                build_generation_plan(command, root, values, 'fail', allow_absolute=True, mode='global'),
                root,
                dry_run=True,
            )

            planned_actions = plan_post_actions(
                command,
                root,
                values,
                generated,
                allow_absolute=True,
                mode='global',
            )

            self.assertIn((outside / 'note.txt').resolve().as_posix(), planned_actions[0].command_display)
            self.assertIn((outside / 'note.txt').resolve().as_posix(), planned_actions[0].command_display)

    def test_validate_template_variables_checks_global_root_field(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            command_dir = root / '.sprout' / 'commands' / 'demo'
            _write(
                command_dir / 'manifest.json',
                json.dumps(
                    {
                        'name': 'demo',
                        'root': '{{project.root}}/tmp',
                        'assets': [{'type': 'dir', 'path': 'x'}],
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
            )
            command = load_command_spec(command_dir)

            issues = validate_template_variables(command, is_global=True)

            self.assertTrue(any(issue.template_path == 'root' for issue in issues))
            self.assertTrue(any('project.root' in issue.message for issue in issues))


if __name__ == '__main__':
    unittest.main()
