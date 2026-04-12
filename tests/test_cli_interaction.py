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
    command_dir = root / '.sprout' / 'commands' / 'issue'
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
            command_dir = root / '.sprout' / 'commands' / 'issue'
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


if __name__ == '__main__':
    unittest.main()
