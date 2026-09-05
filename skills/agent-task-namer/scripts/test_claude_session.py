"""Run with python3 scripts/test_claude_session.py; uses only a mocked SDK."""

import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import claude_session as bridge


SESSION = "550e8400-e29b-41d4-a716-446655440000"
OTHER = "550e8400-e29b-41d4-a716-446655440001"
TITLE = "🐛 修复 | 260904 | 登录回调失败"


class ClaudeSessionTest(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = str(Path(self.temp.name).resolve())
        self.info = SimpleNamespace(
            session_id=SESSION, cwd=self.directory, summary="Automatic summary",
            custom_title=None, created_at=1788480000000, last_modified=9999999999999,
        )
        self.sdk = SimpleNamespace(
            get_session_info=Mock(return_value=self.info),
            get_session_messages=Mock(return_value=[]), rename_session=Mock(),
        )
        self.sdk.rename_session.side_effect = self.rename
        self.request = {
            "action": "inspect", "session_id": SESSION,
            "trusted_session_id": SESSION, "directory": self.directory,
        }

    def rename(self, session_id, title, directory):
        self.assertEqual((session_id, directory), (SESSION, self.directory))
        self.info.custom_title = title

    def run_request(self, **changes):
        return bridge.handle_request({**self.request, **changes}, self.sdk)

    def rename_request(self, **changes):
        return self.run_request(**{
            "action": "rename", "title": TITLE, "expected_title": self.info.summary,
            "mode": "explicit", **changes,
        })

    def message(self, role, content, **changes):
        return SimpleNamespace(**{
            "session_id": SESSION, "type": role, "message": {"role": role, "content": content},
            "parent_tool_use_id": None, "parent_agent_id": None, **changes,
        })

    def test_inspect_verified_metadata_without_date_fallback(self):
        result = self.run_request()
        self.assertEqual(result["created_at_iso"], "2026-09-04T00:00:00Z")
        self.assertEqual(result["summary"], "Automatic summary")
        self.sdk.get_session_info.assert_called_once_with(SESSION, directory=self.directory)
        for invalid in (None, True, "1788480000000", -1, float("nan"), 10 ** 400):
            with self.subTest(created_at=invalid):
                self.info.created_at = invalid
                result = self.run_request()
                self.assertIsNone(result["created_at"])
                self.assertNotIn("created_at_iso", result)
        self.assertFalse(result["write_attempted"])

    def test_invalid_request_never_calls_sdk(self):
        for changes in (
            {"action": "list"}, {"session_id": "not-uuid"}, {"trusted_session_id": OTHER},
            {"directory": "."}, {"directory": self.directory + "/missing"},
            {"client": "codex"}, {"client": "unknown"}, {"trusted_session_id": None},
            {"session_id": "${CLAUDE_SESSION_ID}", "trusted_session_id": "${CLAUDE_SESSION_ID}"},
        ):
            with self.subTest(changes=changes):
                self.assertEqual(self.run_request(**changes)["status"], "invalid_request")
        for invalid in (None, [], "inspect"):
            self.assertEqual(bridge.handle_request(invalid, self.sdk)["status"], "invalid_request")
        for field in ("session_id", "trusted_session_id", "directory"):
            request = self.request.copy()
            del request[field]
            self.assertEqual(bridge.handle_request(request, self.sdk)["status"], "invalid_request")
        self.sdk.get_session_info.assert_not_called()
        self.sdk.rename_session.assert_not_called()

    def test_metadata_identity_and_directory_fail_closed(self):
        for changes in ({"session_id": OTHER}, {"cwd": None}, {"cwd": "."}, {"cwd": "/"}):
            original = vars(self.info).copy()
            with self.subTest(changes=changes):
                vars(self.info).update(changes)
                self.assertEqual(self.rename_request()["status"], "identity_mismatch")
                vars(self.info).update(original)
        alias = Path(self.directory) / "alias"
        alias.symlink_to(self.directory, target_is_directory=True)
        self.info.cwd = str(alias)
        self.assertEqual(self.run_request(directory=str(alias))["status"], "ok")
        self.sdk.get_session_info.return_value = None
        self.assertEqual(self.run_request()["status"], "not_found")
        self.sdk.rename_session.assert_not_called()

    def test_missing_sdk_functions_and_errors_are_sanitized(self):
        with patch.object(bridge, "import_module", side_effect=ImportError("private data")):
            result = bridge.handle_request(self.request)
            self.assertEqual(result["reason"], "sdk_missing")
        for function, action in (("get_session_info", "inspect"), ("get_session_messages", "history"), ("rename_session", "rename")):
            original = getattr(self.sdk, function)
            setattr(self.sdk, function, None)
            result = self.rename_request() if action == "rename" else self.run_request(action=action)
            self.assertEqual(result["reason"], "sdk_function_missing")
            setattr(self.sdk, function, original)
        self.sdk.get_session_info.side_effect = RuntimeError("private transcript and token")
        result = self.run_request()
        self.assertEqual(result["reason"], "inspect_failed")
        self.assertNotIn("private", json.dumps(result))

    def test_rename_validates_titles_and_authorization(self):
        for title in (None, 1, "", "  ", " leading", "trailing ", "bad\ncontext", "bad\u0000context", "bad\ud800", "bad\u2028context"):
            with self.subTest(title=repr(title)):
                self.assertEqual(self.rename_request(title=title)["status"], "invalid_request")
        for changes in ({"mode": "unknown"}, {"mode": None}, {"expected_title": None}):
            self.assertEqual(self.rename_request(**changes)["status"], "invalid_request")
        for source in (None, "resume", "clear", "compact", "fork"):
            self.assertEqual(self.rename_request(mode="automatic", source=source, first_turn=True)["status"], "invalid_request")
        for first_turn in (None, False, 1, "true"):
            self.assertEqual(self.rename_request(mode="automatic", source="startup", first_turn=first_turn)["status"], "invalid_request")
        self.sdk.rename_session.assert_not_called()

    def test_automatic_preserves_custom_titles_and_requires_creation_date(self):
        for custom_title in ("User title", "", TITLE):
            self.info.custom_title = custom_title
            result = self.rename_request(mode="automatic", source="startup", first_turn=True)
            self.assertEqual((result["status"], result["reason"]), ("skipped", "custom_title_exists"))
        self.info.custom_title = None
        self.info.created_at = None
        result = self.rename_request(mode="automatic", source="startup", first_turn=True)
        self.assertEqual(result["reason"], "creation_time_missing")
        self.sdk.rename_session.assert_not_called()
        self.info.created_at = 1788480000000
        self.assertEqual(self.rename_request(mode="automatic", source="startup", first_turn=True)["status"], "verified")
        self.sdk.rename_session.assert_called_once()

    def test_effective_title_conflict_idempotency_and_exact_unicode(self):
        self.info.custom_title = "My old title"
        self.assertEqual(self.rename_request()["status"], "conflict")
        self.sdk.rename_session.assert_not_called()
        result = self.rename_request(expected_title="My old title")
        self.assertEqual((result["status"], result["summary"], result["custom_title"]), ("verified", TITLE, TITLE))
        self.assertTrue(result["write_attempted"])
        self.assertTrue(result["write_succeeded"])
        self.sdk.rename_session.assert_called_once_with(SESSION, TITLE, directory=self.directory)
        result = self.rename_request(expected_title=TITLE)
        self.assertEqual(result["status"], "verified")
        self.assertFalse(result["write_attempted"])
        self.sdk.rename_session.assert_called_once()

    def test_existing_multiline_titles_are_data(self):
        self.info.custom_title = "Old\ttitle\nwith a second line"
        self.assertEqual(self.run_request()["summary"], self.info.custom_title)
        result = self.rename_request(expected_title=self.info.custom_title)
        self.assertEqual(result["status"], "verified")
        self.sdk.rename_session.assert_called_once()

    def test_write_and_readback_failures_do_not_repeat_writes(self):
        self.sdk.rename_session.side_effect = RuntimeError("private write failure")
        result = self.rename_request()
        self.assertEqual(result["status"], "unverified")
        self.assertTrue(result["write_attempted"])
        self.assertFalse(result["write_succeeded"])
        self.sdk.rename_session.assert_called_once()
        self.sdk.rename_session.reset_mock()
        self.sdk.rename_session.side_effect = self.rename
        self.sdk.get_session_info.side_effect = [self.info, RuntimeError("private read failure")]
        result = self.rename_request()
        self.assertEqual(result["reason"], "readback_failed")
        self.assertTrue(result["write_succeeded"])
        self.assertNotIn("private", json.dumps(result))
        self.sdk.rename_session.assert_called_once()

    def test_ambiguous_write_response_can_still_be_verified(self):
        def uncertain_write(*args, **kwargs):
            self.rename(*args, **kwargs)
            raise RuntimeError("private transport failure")
        self.sdk.rename_session.side_effect = uncertain_write
        result = self.rename_request()
        self.assertEqual(result["status"], "verified")
        self.assertTrue(result["write_attempted"])
        self.assertFalse(result["write_succeeded"])
        self.sdk.rename_session.assert_called_once()

    def test_readback_requires_custom_title_and_identity(self):
        self.sdk.rename_session.side_effect = None
        self.sdk.get_session_info.side_effect = [self.info, SimpleNamespace(**{
            **vars(self.info), "summary": TITLE,
        })]
        result = self.rename_request()
        self.assertEqual(result["status"], "unverified")
        self.assertTrue(result["write_succeeded"])
        self.sdk.rename_session.reset_mock()
        self.sdk.get_session_info.side_effect = [self.info, SimpleNamespace(**{
            **vars(self.info), "session_id": OTHER, "custom_title": TITLE,
        })]
        result = self.rename_request()
        self.assertEqual(result["reason"], "readback_identity_unverified")
        self.sdk.rename_session.assert_called_once()

    def test_history_filters_tools_subagents_and_paginates_raw_messages(self):
        self.sdk.get_session_messages.return_value = [
            self.message("user", [{"type": "tool_result", "content": "secret result"}]),
            self.message("assistant", [{"type": "tool_use", "input": "secret call"}, {"type": "text", "text": "visible answer"}]),
            self.message("user", "child text", parent_tool_use_id="tool-id"),
            self.message("user", "next page"),
        ]
        result = self.run_request(action="history", offset=5, limit=3)
        self.assertEqual(result["messages"], [{"role": "assistant", "text": "visible answer", "truncated": False}])
        self.assertEqual(result["next_offset"], 8)
        self.sdk.get_session_messages.assert_called_once_with(SESSION, directory=self.directory, offset=5, limit=4)
        self.assertNotIn("secret", json.dumps(result))
        self.sdk.get_session_messages.return_value = [self.message("user", "界" * 4001)]
        result = self.run_request(action="history")
        self.assertEqual(len(result["messages"][0]["text"]), 4000)
        self.assertTrue(result["messages"][0]["truncated"])
        self.assertIsNone(result["next_offset"])
        self.sdk.get_session_messages.return_value = [self.message("user", "other session", session_id=OTHER)]
        self.assertEqual(self.run_request(action="history")["status"], "identity_mismatch")

    def test_history_bounds_and_sanitized_error(self):
        for changes in ({"limit": 0}, {"limit": 21}, {"limit": True}, {"offset": -1}, {"offset": 100001}, {"offset": "0"}):
            self.assertEqual(self.run_request(action="history", **changes)["status"], "invalid_request")
        self.sdk.get_session_messages.assert_not_called()
        self.sdk.get_session_messages.side_effect = RuntimeError("secret transcript")
        result = self.run_request(action="history")
        self.assertEqual(result["reason"], "history_failed")
        self.assertNotIn("secret", json.dumps(result))

    def test_history_skips_invalid_content_without_losing_valid_messages(self):
        for invalid in (None, True, 42, {"type": "text", "text": "malformed content"}):
            with self.subTest(content=invalid):
                self.sdk.get_session_messages.return_value = [
                    self.message("assistant", invalid),
                    self.message("user", "Actual task goal"),
                    self.message("assistant", "Next page"),
                ]
                result = self.run_request(action="history", offset=5, limit=2)
                self.assertEqual(result["status"], "ok")
                self.assertEqual(result["messages"], [
                    {"role": "user", "text": "Actual task goal", "truncated": False},
                ])
                self.assertEqual(result["next_offset"], 7)
        self.sdk.rename_session.assert_not_called()

    def test_json_input_and_unicode_output(self):
        title = "📝 文档 | 'single' \"double\" | $(literal) `literal`"
        request = {**self.request, "action": "rename", "mode": "explicit", "expected_title": self.info.summary, "title": title}
        output = io.StringIO()
        with patch.object(bridge.sys, "stdin", io.StringIO(json.dumps(request, ensure_ascii=False))), patch.object(bridge.sys, "stdout", output), patch.object(bridge, "import_module", return_value=self.sdk):
            bridge.main()
        self.assertEqual(json.loads(output.getvalue())["custom_title"], title)
        self.sdk.rename_session.assert_called_once_with(SESSION, title, directory=self.directory)
        for raw in ("bad JSON", "null", "[]", "x" * 65537):
            output = io.StringIO()
            with patch.object(bridge.sys, "stdin", io.StringIO(raw)), patch.object(bridge.sys, "stdout", output):
                bridge.main()
            self.assertEqual(json.loads(output.getvalue())["status"], "invalid_request")

    def test_deeply_nested_json_returns_invalid_request_without_loading_sdk(self):
        raw = "[" * 1100 + "0" + "]" * 1100
        output = io.StringIO()
        with patch.object(bridge.sys, "stdin", io.StringIO(raw)), patch.object(bridge.sys, "stdout", output), patch.object(bridge, "import_module") as load_sdk:
            bridge.main()
        self.assertEqual(json.loads(output.getvalue()), {
            "status": "invalid_request", "write_attempted": False, "write_succeeded": False,
        })
        load_sdk.assert_not_called()


if __name__ == "__main__":
    unittest.main()
