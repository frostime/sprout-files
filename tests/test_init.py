from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from sprout.scaffold import initialize_workspace


class InitTests(unittest.TestCase):
    def test_init_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            first = initialize_workspace(root, profile="minimal", profile_file=None, with_examples=True)
            self.assertTrue((root / ".sprout" / "config.json").exists())
            self.assertTrue((root / ".sprout" / "skills" / "sprout-authoring" / "SKILL.md").exists())
            self.assertTrue((root / ".sprout" / "commands" / "issue" / "manifest.json").exists())
            self.assertGreater(len(first.created), 0)

            custom_manifest = root / ".sprout" / "commands" / "issue" / "manifest.json"
            custom_manifest.write_text("{\"name\":\"issue\"}\n", encoding="utf-8")

            second = initialize_workspace(root, profile="minimal", profile_file=None, with_examples=True)
            self.assertEqual(custom_manifest.read_text(encoding="utf-8"), "{\"name\":\"issue\"}\n")
            self.assertGreater(len(second.skipped), 0)

    def test_init_with_profile_file(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            profile_file = root / "profile.json"
            profile_file.write_text(
                json.dumps(
                    {
                        "directories": ["custom/dir"],
                        "files": [
                            {"path": "custom/readme.txt", "content": "hello"},
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            initialize_workspace(
                root,
                profile="minimal",
                profile_file=profile_file,
                with_examples=False,
            )

            self.assertTrue((root / ".sprout" / "custom" / "dir").is_dir())
            self.assertEqual(
                (root / ".sprout" / "custom" / "readme.txt").read_text(encoding="utf-8"),
                "hello",
            )


if __name__ == "__main__":
    unittest.main()
