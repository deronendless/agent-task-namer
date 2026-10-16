"""Check the Claude Code plugin packaging without installing it."""

import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest


REPOSITORY = Path(__file__).resolve().parents[1]
MARKETPLACE = REPOSITORY / ".claude-plugin/marketplace.json"
MANIFEST = REPOSITORY / ".claude-plugin/plugin.json"
AUTOMATIC = REPOSITORY / "skills/agent-task-namer/references/automatic.md"
SHARED_SCRIPT = REPOSITORY / "skills/agent-task-namer/scripts/session_start.py"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def as_list(value):
    return [value] if isinstance(value, str) else [item for item in value or [] if isinstance(item, str)]


def session_start_commands(configuration, source):
    return [
        hook["command"]
        for group in configuration["hooks"]["SessionStart"]
        if re.search(group.get("matcher", ""), source)
        for hook in group["hooks"]
        if hook["type"] == "command"
    ]


class ClaudePluginTest(unittest.TestCase):
    def setUp(self):
        marketplace = load(MARKETPLACE)
        self.entry = marketplace["plugins"][0]
        self.plugin_root = (REPOSITORY / self.entry["source"]).resolve()
        self.manifest = load(MANIFEST)

    def assert_inside(self, root, target):
        self.assertTrue(target == root or root in target.parents, f"{target} escapes {root}")

    def resolve(self, relative):
        self.assertTrue(relative.startswith("./"), relative)
        self.assertNotIn("..", relative)
        target = (self.plugin_root / relative).resolve()
        self.assert_inside(self.plugin_root, target)
        self.assertFalse(target.is_symlink())
        return target

    def test_marketplace_entry_publishes_the_repository_root(self):
        marketplace = load(MARKETPLACE)
        self.assertEqual(marketplace["name"], "agent-task-namer")
        self.assertTrue(marketplace["owner"]["name"])
        self.assertEqual(len(marketplace["plugins"]), 1)
        self.assertEqual(self.plugin_root, REPOSITORY.resolve())
        self.assertEqual(self.entry["name"], self.manifest["name"])
        self.assertNotIn("version", self.entry, "plugin.json owns the version")
        self.assertNotIn("hooks", self.entry, "hooks live in the plugin, not the catalog entry")
        self.assertFalse((self.plugin_root / "CLAUDE.md").exists())

    def test_manifest_matches_the_codex_release_and_resolves_every_path(self):
        codex = load(REPOSITORY / ".codex-plugin/plugin.json")
        self.assertEqual(self.manifest["name"], codex["name"])
        self.assertEqual(self.manifest["version"], codex["version"])
        self.assertEqual(self.manifest["repository"], codex["repository"])
        self.assertEqual(self.manifest["license"], codex["license"])
        self.assertRegex(self.manifest["name"], r"^[a-z0-9]+(-[a-z0-9]+)*$")
        self.assertRegex(self.manifest["version"], r"^\d+\.\d+\.\d+$")
        for key in ("skills", "commands", "agents", "hooks", "outputStyles", "workflows"):
            for relative in as_list(self.manifest.get(key)):
                with self.subTest(key=key, relative=relative):
                    self.assertTrue(self.resolve(relative).exists())

    def test_manifest_skills_directory_is_the_shared_skill(self):
        skills = [self.resolve(relative) for relative in as_list(self.manifest["skills"])]
        self.assertEqual(skills, [(REPOSITORY / "skills").resolve()])
        entry = skills[0] / "agent-task-namer/SKILL.md"
        self.assertIn(entry, list(skills[0].glob("*/SKILL.md")))
        frontmatter = entry.read_text(encoding="utf-8").split("---")[1]
        self.assertIn("name: agent-task-namer", frontmatter)
        self.assertTrue(SHARED_SCRIPT.is_file())

    def test_bundled_hook_resolves_to_the_shared_script(self):
        hook_files = [self.resolve(relative) for relative in as_list(self.manifest["hooks"])]
        self.assertEqual(len(hook_files), 1)
        self.assertFalse((REPOSITORY / "hooks/hooks.json").exists(),
                         "Claude Code always loads hooks/hooks.json, so neither client may use that name")
        codex_hooks = (REPOSITORY / load(REPOSITORY / ".codex-plugin/plugin.json")["hooks"]).resolve()
        self.assertNotEqual(hook_files[0], codex_hooks, "the Codex hook uses PLUGIN_ROOT and no client flag")
        configuration = load(hook_files[0])
        self.assertIn("hooks", configuration, "plugin hook files wrap the event map in a hooks key")
        groups = configuration["hooks"]["SessionStart"]
        self.assertEqual(len(groups), 1)
        documented = re.search(r'"matcher": "([^"]+)"[^}]*--client claude-code',
                               AUTOMATIC.read_text(encoding="utf-8"), re.S)
        self.assertIsNotNone(documented, "automatic.md must document the Claude matcher")
        self.assertEqual(groups[0]["matcher"], documented.group(1))
        for source in ("startup", "resume", "clear", "compact", "fork"):
            self.assertTrue(re.search(groups[0]["matcher"], source), source)
        self.assertFalse(re.search(groups[0]["matcher"], "other"))
        hooks = groups[0]["hooks"]
        self.assertEqual(len(hooks), 1)
        hook = hooks[0]
        self.assertEqual(hook["type"], "command")
        self.assertLessEqual(hook["timeout"], 10)
        self.assertNotIn("additionalContextLimit", hook, "Codex-only field")
        self.assertIn('"${CLAUDE_PLUGIN_ROOT}/', hook["command"], "quote the plugin root")
        self.assertNotIn("${PLUGIN_ROOT}", hook["command"], "Codex-only variable")
        self.assertIn("--client claude-code", hook["command"])
        referenced = re.findall(r'\$\{CLAUDE_PLUGIN_ROOT\}/([^"\s]+)', hook["command"])
        self.assertEqual(len(referenced), 1)
        self.assertEqual(self.resolve(f"./{referenced[0]}"), SHARED_SCRIPT.resolve())

    def test_installed_copy_runs_the_hook_from_another_working_directory(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        # Claude Code copies the whole plugin root into its versioned cache directory.
        root = (Path(temporary.name) / "中文 plugin cache" / "agent-task-namer" / self.manifest["version"]).resolve()
        shutil.copytree(self.plugin_root, root,
                        ignore=shutil.ignore_patterns(".git", "__pycache__", "*.py[cod]"))
        for relative in (*as_list(self.manifest["skills"]), *as_list(self.manifest["hooks"])):
            self.assertTrue((root / relative).exists(), relative)
        self.assertTrue((root / "skills/agent-task-namer/SKILL.md").is_file())
        project = Path(temporary.name) / "unrelated project"
        project.mkdir()
        configuration = load(root / as_list(self.manifest["hooks"])[0])
        env = {key: value for key, value in os.environ.items() if key != "PLUGIN_ROOT"}
        env.update(CLAUDE_PLUGIN_ROOT=str(root), PYTHONIOENCODING="ascii")
        expectations = {"startup": "CLAUDE STARTUP/root", "fork": "CLAUDE LIFECYCLE/root"}
        for source, prefix in expectations.items():
            commands = session_start_commands(configuration, source)
            self.assertEqual(len(commands), 1)
            with self.subTest(source=source):
                result = subprocess.run(
                    commands[0], shell=True, cwd=project, env=env,
                    input=json.dumps({"hook_event_name": "SessionStart", "source": source,
                                      "session_id": "synthetic_claude_plugin_session",
                                      "cwd": str(project)}),
                    text=True, encoding="utf-8", capture_output=True, check=True, timeout=10,
                )
                output = json.loads(result.stdout)["hookSpecificOutput"]
                self.assertEqual(output["hookEventName"], "SessionStart")
                self.assertTrue(output["additionalContext"].startswith(prefix))
                self.assertIn(str(root / "skills/agent-task-namer/SKILL.md"), output["additionalContext"])
                self.assertIn("synthetic_claude_plugin_session", output["additionalContext"])
                self.assertEqual(result.stderr, "")


if __name__ == "__main__":
    unittest.main()
