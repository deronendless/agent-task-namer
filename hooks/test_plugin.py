"""Test the packaged plugin in a temporary directory without installing it."""

import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from urllib.parse import urlsplit


REPOSITORY = Path(__file__).resolve().parents[1]


class PluginTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = (Path(temporary.name) / "中文 plugin cache" / "agent-task-namer").resolve()
        self.root.mkdir(parents=True)
        for directory in (".codex-plugin", "hooks", "skills"):
            shutil.copytree(REPOSITORY / directory, self.root / directory,
                            ignore=shutil.ignore_patterns("__pycache__", "*.py[cod]"))
        self.project = Path(temporary.name) / "unrelated project"
        self.project.mkdir()

    def assert_self_contained_skill(self, skill):
        for relative in ("SKILL.md", "agents/openai.yaml", "scripts/session_start.py",
                         "scripts/claude_session.py", "scripts/requirements-claude.txt"):
            with self.subTest(relative=relative):
                self.assertTrue((skill / relative).is_file())
        self.assertEqual((skill / "LICENSE").read_bytes(), (REPOSITORY / "LICENSE").read_bytes())
        for document in skill.rglob("*.md"):
            links = re.findall(r"\[[^\]]*\]\(([^)\n]+)\)", document.read_text(encoding="utf-8"))
            for link in links:
                parsed = urlsplit(link)
                if parsed.scheme or parsed.netloc or not parsed.path:
                    continue
                target = (document.parent / parsed.path).resolve()
                with self.subTest(document=document, link=link):
                    self.assertIn(skill, target.parents)
                    self.assertTrue(target.is_file())

    def test_manifest_discovers_skill_with_readable_local_workflow(self):
        manifest = json.loads((self.root / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
        skill_directory = self.root / manifest["skills"]
        entry = skill_directory / "agent-task-namer/SKILL.md"
        self.assertIn(entry, skill_directory.glob("*/SKILL.md"))
        self.assert_self_contained_skill(entry.parent.resolve())

    def test_repository_marketplace_pins_the_release(self):
        manifest = json.loads((REPOSITORY / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
        marketplace = json.loads(
            (REPOSITORY / ".agents/plugins/marketplace.json").read_text(encoding="utf-8")
        )
        self.assertEqual(marketplace["name"], "agent-task-namer")
        self.assertEqual(marketplace["interface"]["displayName"], "Agent Task Namer")
        self.assertEqual(len(marketplace["plugins"]), 1)
        plugin = marketplace["plugins"][0]
        self.assertEqual(plugin["name"], manifest["name"])
        self.assertEqual(plugin["source"], {
            "source": "url",
            "url": f'{manifest["repository"]}.git',
            "ref": f'v{manifest["version"]}',
        })
        self.assertEqual(plugin["policy"], {
            "installation": "AVAILABLE",
            "authentication": "ON_INSTALL",
        })
        self.assertEqual(plugin["category"], manifest["interface"]["category"])

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
        self.assertIn(str(self.root / "skills/agent-task-namer/SKILL.md"), output["additionalContext"])
        self.assertIn("synthetic_plugin_session", output["additionalContext"])
        self.assertIn("authorizes one automatic rename", output["additionalContext"])
        self.assertIn("read_thread", output["additionalContext"])
        self.assertIn("set_thread_title", output["additionalContext"])
        self.assertEqual(result.stderr, "")

    def test_standalone_skill_runs_without_plugin_files(self):
        skill = (self.project / "中文 standalone install" / "agent-task-namer").resolve()
        shutil.copytree(self.root / "skills/agent-task-namer", skill)
        self.assert_self_contained_skill(skill)
        for client_args in ((), ("--client", "claude-code")):
            with self.subTest(client_args=client_args):
                result = subprocess.run(
                    [sys.executable, str(skill / "scripts/session_start.py"), *client_args],
                    cwd=self.project,
                    env={key: value for key, value in {**os.environ, "PYTHONIOENCODING": "ascii"}.items()
                         if key != "PLUGIN_ROOT"},
                    input=json.dumps({"hook_event_name": "SessionStart", "source": "startup",
                                      "session_id": "synthetic_standalone_session", "cwd": str(self.project)}),
                    text=True, encoding="utf-8", capture_output=True, check=True, timeout=10,
                )
                output = json.loads(result.stdout)["hookSpecificOutput"]
                self.assertEqual(output["hookEventName"], "SessionStart")
                self.assertIn(str(skill / "SKILL.md"), output["additionalContext"])
                self.assertIn("synthetic_standalone_session", output["additionalContext"])
                self.assertEqual(result.stderr, "")


if __name__ == "__main__":
    unittest.main()
