"""Test the packaged plugin in a temporary directory without installing it."""

import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest


REPOSITORY = Path(__file__).resolve().parents[1]


class PluginTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = (Path(temporary.name) / "中文 plugin cache" / "agent-task-namer").resolve()
        self.root.mkdir(parents=True)
        for directory in (".codex-plugin", "hooks", "skills", "references"):
            shutil.copytree(REPOSITORY / directory, self.root / directory)
        for relative in ("SKILL.md", "scripts/session_start.py"):
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(REPOSITORY / relative, target)
        self.project = Path(temporary.name) / "unrelated project"
        self.project.mkdir()

    def test_manifest_discovers_skill_with_readable_local_workflow(self):
        manifest = json.loads((self.root / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
        skill_directory = self.root / manifest["skills"]
        entry = skill_directory / "agent-task-namer/SKILL.md"
        self.assertIn(entry, skill_directory.glob("*/SKILL.md"))
        links = re.findall(r"\[[^\]]*\]\(([^)\n]+)\)", entry.read_text(encoding="utf-8"))
        targets = [(entry.parent / link).resolve() for link in links]
        workflow = self.root / "SKILL.md"
        self.assertIn(workflow, targets)
        for target in targets:
            with self.subTest(target=target):
                self.assertIn(self.root, target.parents)
                self.assertTrue(target.read_text(encoding="utf-8").strip())

    def test_packaged_hook_runs_from_another_working_directory(self):
        configuration = json.loads((self.root / "hooks/hooks.json").read_text(encoding="utf-8"))
        commands = [
            hook["command"]
            for group in configuration["hooks"]["SessionStart"]
            if re.search(group.get("matcher", ""), "startup")
            for hook in group["hooks"]
            if hook["type"] == "command"
        ]
        self.assertEqual(len(commands), 1)
        result = subprocess.run(
            commands[0], shell=True, cwd=self.project,
            env={**os.environ, "PLUGIN_ROOT": str(self.root), "PYTHONIOENCODING": "ascii"},
            input=json.dumps({"hook_event_name": "SessionStart", "source": "startup",
                              "session_id": "synthetic_plugin_session", "cwd": str(self.project)}),
            text=True, encoding="utf-8", capture_output=True, check=True, timeout=10,
        )
        output = json.loads(result.stdout)["hookSpecificOutput"]
        self.assertEqual(output["hookEventName"], "SessionStart")
        self.assertIn(str(self.root / "SKILL.md"), output["additionalContext"])
        self.assertIn("synthetic_plugin_session", output["additionalContext"])
        self.assertEqual(result.stderr, "")


if __name__ == "__main__":
    unittest.main()
