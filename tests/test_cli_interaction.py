from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from sprout.cli import main


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')


def _create_workspace(root: Path) -> None:
    command_dir = root / '.sprout' / '__new__' / 'issue'
    _write(
        command_dir / 'manifest.json',
        json.dumps(
            {
                'name': 'issue',
                'description': 'Create an issue document',
                'inputs': [
                    {'name': 'name', 'type': 'string', 'description': 'Issue slug'},
                    {'name': 'type', 'type': 'enum', 'enum': ['bug', 'feat'], 'default': 'bug'},
                ],
                'assets': [
                    {'type': 'dir', 'path': 'issues'},
                    {'type': 'file', 'path': 'issues/{{name}}.md', 'template': 'issue.md'},
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
    )
    _write(command_dir / 'issue.md', '# {{name}}')


class CliInteractionTests(unittest.TestCase):
    def test_doc_list_shows_builtin_documents(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = main(['doc', 'list'])

        self.assertEqual(exit_code, 0)
        self.assertIn('user-guide', stdout.getvalue())
        self.assertIn('command-authoring-guide', stdout.getvalue())

    def test_doc_show_prints_builtin_document(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = main(['doc', 'show', 'command-authoring-guide'])

        self.assertEqual(exit_code, 0)
        self.assertIn('Sprout Command Authoring Guide', stdout.getvalue())

    def test_builtin_creates_manifest_template(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / '.sprout').mkdir()

            stdout = io.StringIO()
            stderr = io.StringIO()
            with patch('pathlib.Path.cwd', return_value=root):
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    exit_code = main(['builtin', 'demo'])

            self.assertEqual(exit_code, 0)
            manifest = root / '.sprout' / '__new__' / 'demo' / 'manifest.yaml'
            self.assertTrue(manifest.exists())
            content = manifest.read_text(encoding='utf-8')
            self.assertIn('name: demo', content)
            self.assertIn('Replace this inline content with your real template.', content)

    def test_buildin_alias_works(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / '.sprout').mkdir()

            stdout = io.StringIO()
            stderr = io.StringIO()
            with patch('pathlib.Path.cwd', return_value=root):
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    exit_code = main(['buildin', 'demo'])

            self.assertEqual(exit_code, 0)
            self.assertTrue((root / '.sprout' / '__new__' / 'demo' / 'manifest.yaml').exists())

    def test_builtin_migrates_legacy_commands_dir(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            legacy_command = root / '.sprout' / 'commands' / 'issue'
            _write(
                legacy_command / 'manifest.json',
                json.dumps({'name': 'issue', 'assets': [{'type': 'dir', 'path': 'issues'}]}, ensure_ascii=False, indent=2),
            )

            stdout = io.StringIO()
            stderr = io.StringIO()
            with patch('pathlib.Path.cwd', return_value=root):
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    exit_code = main(['builtin', 'demo'])

            self.assertEqual(exit_code, 0)
            self.assertTrue((root / '.sprout' / '__new__' / 'issue' / 'manifest.json').exists())
            self.assertTrue((root / '.sprout' / '__new__' / 'demo' / 'manifest.yaml').exists())

    def test_unknown_command_shows_suggestion(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _create_workspace(root)

            stdout = io.StringIO()
            stderr = io.StringIO()
            with patch('pathlib.Path.cwd', return_value=root):
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    exit_code = main(['new', 'isue'])

            self.assertEqual(exit_code, 1)
            self.assertIn('Did you mean: issue', stderr.getvalue())
            self.assertIn('Create an issue document', stderr.getvalue())

    def test_non_tty_missing_required_inputs_do_not_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _create_workspace(root)

            stdout = io.StringIO()
            stderr = io.StringIO()
            with patch('pathlib.Path.cwd', return_value=root), patch('sprout.cli._is_tty_session', return_value=False):
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    exit_code = main(['new', 'issue'])

            self.assertEqual(exit_code, 1)
            self.assertIn('Missing required inputs: name', stderr.getvalue())
            self.assertIn('--json', stderr.getvalue())

    def test_interactive_mode_requires_tty(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _create_workspace(root)

            stdout = io.StringIO()
            stderr = io.StringIO()
            with patch('pathlib.Path.cwd', return_value=root), patch('sprout.cli._is_tty_session', return_value=False):
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    exit_code = main(['new', 'issue', '-i'])

            self.assertEqual(exit_code, 1)
            self.assertIn('Interactive mode requires a TTY', stderr.getvalue())

    def test_json_input_and_set_override(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _create_workspace(root)

            stdout = io.StringIO()
            stderr = io.StringIO()
            with patch('pathlib.Path.cwd', return_value=root):
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    exit_code = main([
                        'new',
                        'issue',
                        '--json',
                        '{"name":"from json","type":"bug"}',
                        '--set',
                        'name=from-set',
                    ])

            self.assertEqual(exit_code, 0)
            self.assertTrue((root / 'issues' / 'from-set.md').exists())

    def test_interactive_summary_and_confirm(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _create_workspace(root)

            stdout = io.StringIO()
            stderr = io.StringIO()
            answers = iter(['', 'task-from-prompt', ''])
            with patch('pathlib.Path.cwd', return_value=root), patch('sprout.cli._is_tty_session', return_value=True), patch('builtins.input', side_effect=lambda prompt='': next(answers)):
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    exit_code = main(['new', 'issue'])

            self.assertEqual(exit_code, 0)
            self.assertIn('Interactive summary', stdout.getvalue())
            self.assertTrue((root / 'issues' / 'task-from-prompt.md').exists())

    def test_dry_run_previews_actions_without_executing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            command_dir = root / '.sprout' / '__new__' / 'issue'
            marker = root / 'marker.txt'
            _write(
                command_dir / 'manifest.json',
                json.dumps(
                    {
                        'name': 'issue',
                        'description': 'Create an issue document',
                        'inputs': [{'name': 'name', 'type': 'string', 'description': 'Issue slug'}],
                        'assets': [
                            {'type': 'dir', 'path': 'issues/{{name}}', 'ref': 'issue_dir'},
                        ],
                        'actions': [
                            {
                                'phase': 'post',
                                'run': ['python', '-c', f"from pathlib import Path; Path(r'{marker.as_posix()}').write_text('x', encoding='utf-8')"],
                                'cwd': '{{assets.issue_dir}}',
                            }
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
            )

            stdout = io.StringIO()
            stderr = io.StringIO()
            with patch('pathlib.Path.cwd', return_value=root):
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    exit_code = main(['new', 'issue', 'name=test', '--dry-run'])

            self.assertEqual(exit_code, 0)
            self.assertIn('> ACTION [post]', stdout.getvalue())
            self.assertFalse(marker.exists())

    def test_interactive_cancel_stops_without_writing_files(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _create_workspace(root)

            stdout = io.StringIO()
            stderr = io.StringIO()
            answers = iter(['', 'q'])
            with patch('pathlib.Path.cwd', return_value=root), patch('sprout.cli._is_tty_session', return_value=True), patch('builtins.input', side_effect=lambda prompt='': next(answers)):
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    exit_code = main(['new', 'issue'])

            self.assertEqual(exit_code, 1)
            self.assertIn('Cancelled. No files were created.', stderr.getvalue())
            self.assertFalse((root / 'issues').exists())

    def test_init_global_creates_directory(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            global_dir = Path(td) / 'sprout'
            with patch('sprout.core.GLOBAL_SPROUT_DIR', global_dir), \
                 patch('sprout.scaffold.GLOBAL_SPROUT_DIR', global_dir):
                stdout = io.StringIO()
                stderr = io.StringIO()
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    exit_code = main(['init', '--global'])

                self.assertEqual(exit_code, 0)
                self.assertTrue((global_dir / '__new__').is_dir())
                self.assertTrue((global_dir / 'config.yaml').exists())
                self.assertIn('Global', stdout.getvalue())

    def test_list_global_shows_global_commands(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            global_dir = Path(td) / 'sprout'
            cmd_dir = global_dir / '__new__' / 'mycmd'
            cmd_dir.mkdir(parents=True)
            _write(
                cmd_dir / 'manifest.json',
                json.dumps({'name': 'mycmd', 'assets': [{'type': 'dir', 'path': 'out'}]}, ensure_ascii=False, indent=2),
            )
            _write(global_dir / 'config.yaml', 'conflict: fail\n')
            with patch('sprout.core.GLOBAL_SPROUT_DIR', global_dir):
                stdout = io.StringIO()
                stderr = io.StringIO()
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    exit_code = main(['list', '-g'])

                self.assertEqual(exit_code, 0)
                self.assertIn('mycmd', stdout.getvalue())
                self.assertIn('Global directory', stdout.getvalue())

    def test_new_global_generates_files(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            global_dir = Path(td) / 'sprout'
            cmd_dir = global_dir / '__new__' / 'note'
            cmd_dir.mkdir(parents=True)
            _write(
                cmd_dir / 'manifest.json',
                json.dumps({
                    'name': 'note',
                    'inputs': [{'name': 'title', 'type': 'string'}],
                    'assets': [{'type': 'file', 'path': '{{title}}.txt', 'content': '{{title}}'}],
                }, ensure_ascii=False, indent=2),
            )
            _write(global_dir / 'config.yaml', 'conflict: skip\n')
            output_dir = Path(td) / 'output'
            output_dir.mkdir()
            with patch('sprout.core.GLOBAL_SPROUT_DIR', global_dir):
                stdout = io.StringIO()
                stderr = io.StringIO()
                with patch('pathlib.Path.cwd', return_value=output_dir):
                    with redirect_stdout(stdout), redirect_stderr(stderr):
                        exit_code = main(['new', '-g', 'note', 'title=hello'])

                self.assertEqual(exit_code, 0)
                self.assertTrue((output_dir / 'hello.txt').exists())
                self.assertIn('hello', (output_dir / 'hello.txt').read_text(encoding='utf-8'))

    def test_doctor_global_checks_global_registry(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            global_dir = Path(td) / 'sprout'
            global_dir.mkdir()
            (global_dir / '__new__').mkdir()
            _write(global_dir / 'config.yaml', 'conflict: fail\n')
            with patch('sprout.core.GLOBAL_SPROUT_DIR', global_dir):
                stdout = io.StringIO()
                stderr = io.StringIO()
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    exit_code = main(['doctor', '-g'])

                self.assertEqual(exit_code, 0)
                self.assertIn('Global directory', stdout.getvalue())
                self.assertIn('OK', stdout.getvalue())


if __name__ == '__main__':
    unittest.main()
