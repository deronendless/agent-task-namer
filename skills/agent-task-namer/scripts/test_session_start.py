"""Run with python3 test_session_start.py. No live Codex tools are invoked."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).with_name("session_start.py").resolve()


class SessionStartTest(unittest.TestCase):
    def run_hook(self, event, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args], input=event, text=True,
            capture_output=True, check=True,
        )

    def test_lifecycle_payload(self):
        for source in ("startup", "resume", "clear", "compact"):
            with self.subTest(source=source):
                result = self.run_hook(json.dumps({
                    "hook_event_name": "SessionStart", "source": source,
                    "session_id": "thr_123", "transcript_path": "private-transcript-path",
                }))
                output = json.loads(result.stdout)["hookSpecificOutput"]
                self.assertEqual(output["hookEventName"], "SessionStart")
                self.assertIn("thr_123", output["additionalContext"])
                self.assertIn(str(SCRIPT.parent.parent / "SKILL.md"), output["additionalContext"])
                self.assertNotIn("private-transcript-path", result.stdout)
                self.assertEqual(result.stderr, "")

    def test_codex_startup_is_actionable_and_other_sources_preserve_title(self):
        skill = str(SCRIPT.parent.parent / "SKILL.md")
        event = {"hook_event_name": "SessionStart", "session_id": "thr_123"}
        event["source"] = "startup"
        context = json.loads(self.run_hook(json.dumps(event)).stdout)["hookSpecificOutput"]["additionalContext"]
        for phrase in ("STARTUP/root", f"first read {skill}", "authorizes one automatic rename",
                       "read_thread", "set_thread_title", "omit threadId", "to verify",
                       "If the Skill cannot be read, skip naming", "Root agent only",
                       "subagents must ignore this reminder"):
            self.assertIn(phrase, context)
        self.assertLess(context.index(f"first read {skill}"), context.index("read_thread"))
        self.assertLess(context.index("read_thread"), context.index("set_thread_title"))
        self.assertLess(context.index("set_thread_title"), context.index("to verify"))
        self.assertLess(len(context), 1200)

        for source in ("resume", "clear", "compact"):
            with self.subTest(source=source):
                event["source"] = source
                context = json.loads(self.run_hook(json.dumps(event)).stdout)["hookSpecificOutput"]["additionalContext"]
                self.assertIn(f"source={source}", context)
                self.assertIn("does not authorize automatic naming", context)
                self.assertIn("Preserve the current title", context)
                self.assertNotIn("set_thread_title", context)
                self.assertNotIn("authorizes one automatic rename", context)
                self.assertLess(len(context), 1200)

    def test_irrelevant_or_invalid_input_is_nonblocking(self):
        for payload in ("bad json", "null", "[]", "{}", json.dumps({
            "hook_event_name": "SubagentStart", "source": "startup", "session_id": "thr_123",
        }), json.dumps({
            "hook_event_name": "SessionStart", "source": "startup", "session_id": "bad\ncontext",
        })):
            with self.subTest(payload=payload):
                self.assertEqual(self.run_hook(payload).stdout, "")

    def test_excessive_json_depth_is_nonblocking(self):
        payload = "[" * 2000 + "]" * 2000
        for args in ((), ("--client", "claude-code")):
            with self.subTest(args=args):
                result = self.run_hook(payload, *args)
                self.assertEqual(result.stdout, "")
                self.assertEqual(result.stderr, "")

    def test_unicode_install_path_with_ascii_stdout(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill = (Path(tmp) / "中文 skill").resolve()
            (skill / "scripts").mkdir(parents=True)
            (skill / "SKILL.md").write_text("Test skill", encoding="utf-8")
            script = skill / "scripts" / SCRIPT.name
            shutil.copyfile(SCRIPT, script)
            event = {"hook_event_name": "SessionStart", "source": "startup",
                     "session_id": "abc123", "cwd": str(skill)}
            for args in ((), ("--client", "claude-code")):
                with self.subTest(args=args):
                    result = subprocess.run(
                        [sys.executable, str(script), *args], input=json.dumps(event),
                        text=True, capture_output=True, check=True,
                        env={**os.environ, "PYTHONIOENCODING": "ascii"},
                    )
                    output = json.loads(result.stdout)["hookSpecificOutput"]
                    self.assertIn(str(skill / "SKILL.md"), output["additionalContext"])
                    self.assertEqual(result.stderr, "")

    def test_claude_and_subagent_routing(self):
        event = {"hook_event_name": "SessionStart", "source": "startup",
                 "session_id": "abc123", "cwd": str(SCRIPT.parent),
                 "agent_type": "custom-main-agent"}
        context = json.loads(self.run_hook(json.dumps(event), "--client", "claude-code").stdout)["hookSpecificOutput"]["additionalContext"]
        for phrase in ("CLAUDE STARTUP/root", f"first read {SCRIPT.parent.parent / 'SKILL.md'}",
                       '"session_id": "abc123"', "official SDK bridge", "rename once",
                       "inspect custom_title to verify", "If the Skill cannot be read, skip naming",
                       "Root agent only", "subagents must ignore this reminder"):
            self.assertIn(phrase, context)
        self.assertNotIn("set_thread_title", context)
        self.assertLess(len(context), 1200)
        for source in ("startup", "resume", "clear", "compact", "fork"):
            event["source"] = source
            result = self.run_hook(json.dumps(event), "--client", "claude-code")
            context = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
            self.assertIn("CLAUDE", context)
            self.assertIn('"source": "' + source + '"', context)
            self.assertNotIn("set_thread_title", context)
            if source != "startup":
                self.assertIn("does not authorize automatic naming", context)
                self.assertIn("Preserve the current title", context)
                self.assertNotIn("rename once", context)
                self.assertNotIn("authorizes one automatic rename", context)
            self.assertLess(len(context), 1200)
        event["source"] = "startup"
        for field in ("agent_id", "parent_tool_use_id"):
            for args in ((), ("--client", "claude-code")):
                self.assertEqual(self.run_hook(json.dumps({**event, field: "child"}), *args).stdout, "")
        self.assertEqual(self.run_hook(json.dumps({**event, "cwd": "relative"}), "--client", "claude-code").stdout, "")
        result = subprocess.run([sys.executable, str(SCRIPT), "--client", "unknown"],
                                input=json.dumps(event), text=True, capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
