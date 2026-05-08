from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from sprout.core import (
    apply_generation_plan,
    build_generation_plan,
    build_variable_context,
    collect_inputs,
    evaluate_computed_values,
    load_command_spec,
)
from sprout.models import GenerationError, ValidationError


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _build_command(root: Path, *, use_yaml: bool = False) -> Path:
    command_dir = root / ".sprout" / "commands" / "issue"
    manifest = {
        "name": "issue",
        "inputs": [{"name": "name", "type": "string"}],
        "assets": [
            {"type": "dir", "path": "issues"},
            {
                "type": "file",
                "path": "issues/{{name}}.md",
                "template": "issue.md",
            },
        ],
    }
    if use_yaml:
        _write(
            command_dir / "manifest.yaml",
            "name: issue\ninputs:\n  - name: name\n    type: string\nassets:\n  - type: dir\n    path: issues\n  - type: file\n    path: issues/{{name}}.md\n    template: issue.md\n",
        )
    else:
        _write(command_dir / "manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
    _write(command_dir / "issue.md", "# {{name}}")
    return command_dir


class GenerationPolicyTests(unittest.TestCase):
    def test_yaml_manifest_generates_assets(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            command = load_command_spec(_build_command(root, use_yaml=True))

            context = build_variable_context(
                collect_inputs(command, {"name": "yaml-case"}, interactive=False)
            )
            plan = build_generation_plan(command, root, context, "fail")
            apply_generation_plan(plan, root)

            self.assertTrue((root / "issues" / "yaml-case.md").exists())

    def test_fail_policy(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            command = load_command_spec(_build_command(root))

            target = root / "issues" / "dup.md"
            _write(target, "old")

            context = build_variable_context(
                collect_inputs(command, {"name": "dup"}, interactive=False)
            )

            with self.assertRaises(GenerationError):
                build_generation_plan(command, root, context, "fail")

    def test_overwrite_policy(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            command = load_command_spec(_build_command(root))

            target = root / "issues" / "dup.md"
            _write(target, "old")

            context = build_variable_context(
                collect_inputs(command, {"name": "dup"}, interactive=False)
            )

            plan = build_generation_plan(command, root, context, "overwrite")
            results = apply_generation_plan(plan, root)
            self.assertTrue(any(item.action == "overwrite" for item in results))
            self.assertEqual(target.read_text(encoding="utf-8"), "# dup")

    def test_skip_policy(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            command = load_command_spec(_build_command(root))

            target = root / "issues" / "dup.md"
            _write(target, "old")

            context = build_variable_context(
                collect_inputs(command, {"name": "dup"}, interactive=False)
            )

            plan = build_generation_plan(command, root, context, "skip")
            results = apply_generation_plan(plan, root)
            self.assertTrue(any(item.action == "skip" for item in results))
            self.assertEqual(target.read_text(encoding="utf-8"), "old")

    def test_rename_policy(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            command = load_command_spec(_build_command(root))

            target = root / "issues" / "dup.md"
            _write(target, "old")

            context = build_variable_context(
                collect_inputs(command, {"name": "dup"}, interactive=False)
            )

            plan = build_generation_plan(command, root, context, "rename")
            results = apply_generation_plan(plan, root)

            renamed_files = [item.final_path for item in results if item.action == "rename"]
            self.assertGreaterEqual(len(renamed_files), 1)
            self.assertTrue((root / "issues" / "dup_02.md").exists())

    def test_computed_and_conditional_assets(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            command_dir = root / '.sprout' / 'commands' / 'demo'
            _write(
                command_dir / 'manifest.json',
                json.dumps(
                    {
                        'schema': 'sprout.manifest/v1',
                        'name': 'demo',
                        'inputs': [
                            {'name': 'name', 'type': 'string'},
                            {'name': 'with_tests', 'type': 'boolean', 'default': False},
                        ],
                        'computed': [{'name': 'slug', 'expr': "name.lower().replace(' ', '-')"}],
                        'assets': [
                            {'type': 'dir', 'path': 'items/{{slug}}', 'ref': 'item_dir'},
                            {
                                'type': 'file',
                                'path': '{{assets.item_dir.rel_path}}/README.md',
                                'content': '# {{name}}',
                            },
                            {
                                'type': 'file',
                                'when': {'expr': 'with_tests'},
                                'path': '{{assets.item_dir.rel_path}}/test.md',
                                'content': 'test',
                            },
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
            )
            command = load_command_spec(command_dir)
            context = build_variable_context(
                collect_inputs(command, {'name': 'My Task'}, interactive=False)
            )
            evaluate_computed_values(command, context)

            plan = build_generation_plan(command, root, context, 'fail')
            apply_generation_plan(plan, root)

            self.assertTrue((root / 'items' / 'my-task' / 'README.md').exists())
            self.assertFalse((root / 'items' / 'my-task' / 'test.md').exists())

    def test_inactive_asset_does_not_validate_template_and_content_conflict(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            command_dir = root / '.sprout' / 'commands' / 'demo'
            _write(
                command_dir / 'manifest.json',
                json.dumps(
                    {
                        'schema': 'sprout.manifest/v1',
                        'name': 'demo',
                        'inputs': [],
                        'assets': [
                            {
                                'type': 'file',
                                'when': {'expr': 'False'},
                                'path': 'bad.md',
                                'template': 'missing.md',
                                'content': 'bad',
                            },
                            {'type': 'file', 'path': 'ok.md', 'content': 'ok'},
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
            )
            command = load_command_spec(command_dir)
            context = build_variable_context({})

            plan = build_generation_plan(command, root, context, 'fail')
            apply_generation_plan(plan, root)

            self.assertTrue((root / 'ok.md').exists())
            self.assertFalse((root / 'bad.md').exists())

    def test_active_file_asset_requires_exactly_one_source(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            command_dir = root / '.sprout' / 'commands' / 'demo'
            _write(
                command_dir / 'manifest.json',
                json.dumps(
                    {
                        'name': 'demo',
                        'inputs': [],
                        'assets': [
                            {
                                'type': 'file',
                                'path': 'bad.md',
                                'template': 'x.md',
                                'content': 'bad',
                            }
                        ],
                    }
                ),
            )
            command = load_command_spec(command_dir)

            with self.assertRaises(ValidationError) as ctx:
                build_generation_plan(command, root, build_variable_context({}), 'fail')
            self.assertIn('exactly one of template or content', str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
