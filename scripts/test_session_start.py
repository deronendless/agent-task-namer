"""Run with python3 test_session_start.py. No live Codex tools are invoked."""

import json
from pathlib import Path
import subprocess
import sys
import unittest


SCRIPT = Path(__file__).with_name("session_start.py")


class SessionStartTest(unittest.TestCase):
    def run_hook(self, event):
        return subprocess.run(
            [sys.executable, str(SCRIPT)], input=event, text=True,
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


if __name__ == "__main__":
    unittest.main()
