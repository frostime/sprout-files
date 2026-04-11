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
    load_command_spec,
)
from sprout.models import GenerationError


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


if __name__ == "__main__":
    unittest.main()
