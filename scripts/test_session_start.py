"""Run with python3 test_session_start.py. No live Codex tools are invoked."""

import json
from pathlib import Path
import subprocess
import sys
import unittest


SCRIPT = Path(__file__).with_name("session_start.py")


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

    def test_irrelevant_or_invalid_input_is_nonblocking(self):
        for payload in ("bad json", "null", "[]", "{}", json.dumps({
            "hook_event_name": "SubagentStart", "source": "startup", "session_id": "thr_123",
        }), json.dumps({
            "hook_event_name": "SessionStart", "source": "startup", "session_id": "bad\ncontext",
        })):
            with self.subTest(payload=payload):
                self.assertEqual(self.run_hook(payload).stdout, "")

    def test_claude_and_subagent_routing(self):
        event = {"hook_event_name": "SessionStart", "source": "startup",
                 "session_id": "abc123", "cwd": str(SCRIPT.parent),
                 "agent_type": "custom-main-agent"}
        for source in ("startup", "resume", "clear", "compact", "fork"):
            event["source"] = source
            result = self.run_hook(json.dumps(event), "--client", "claude-code")
            context = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
            self.assertIn("Claude Code", context)
            self.assertIn('"source": "' + source + '"', context)
            self.assertNotIn("set_thread_title", context)
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
