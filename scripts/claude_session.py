#!/usr/bin/env python3
"""JSON bridge to official Claude session APIs; never edit transcripts directly."""

from datetime import datetime, timezone
from importlib import import_module
import json
from pathlib import Path
import sys
import unicodedata
from uuid import UUID


def valid_title(value):
    if not isinstance(value, str):
        return False
    if not value.strip():
        return False
    return not any(unicodedata.category(char) in ("Cc", "Cs", "Zl", "Zp") for char in value)


def metadata(info, session_id, directory):
    if info is None:
        return {"status": "not_found"}
    try:
        if not isinstance(info.cwd, str) or not Path(info.cwd).is_absolute():
            return {"status": "identity_mismatch"}
        if str(UUID(info.session_id)) != session_id or Path(info.cwd).resolve(strict=True) != directory:
            return {"status": "identity_mismatch"}
    except (AttributeError, TypeError, ValueError, OSError, RuntimeError):
        return {"status": "identity_mismatch"}
    custom_title = getattr(info, "custom_title", None)
    summary = custom_title if custom_title is not None else getattr(info, "summary", None)
    if not isinstance(summary, str) or (custom_title is not None and not isinstance(custom_title, str)):
        return {"status": "invalid_metadata"}
    created_at = getattr(info, "created_at", None)
    if type(created_at) is not int or created_at < 0:
        created_at = None
    result = {
        "status": "ok", "session_id": session_id, "directory": str(directory),
        "summary": summary, "custom_title": custom_title, "created_at": created_at,
    }
    if created_at is not None:
        try:
            result["created_at_iso"] = datetime.fromtimestamp(created_at / 1000, timezone.utc).isoformat().replace("+00:00", "Z")
        except (ValueError, OverflowError, OSError):
            result["created_at"] = None
    return result


def handle_request(request, sdk=None):
    result = process_request(request, sdk)
    result.setdefault("write_attempted", False)
    result.setdefault("write_succeeded", False)
    return result


def process_request(request, sdk):
    if not isinstance(request, dict) or request.get("action") not in ("inspect", "history", "rename"):
        return {"status": "invalid_request"}
    try:
        session_id = str(UUID(request["session_id"]))
        trusted_session_id = str(UUID(request["trusted_session_id"]))
        path = request["directory"]
        if not isinstance(path, str) or not Path(path).is_absolute():
            return {"status": "invalid_request"}
        directory = Path(path).resolve(strict=True)
        if not directory.is_dir() or trusted_session_id != session_id or request.get("client", "claude-code") != "claude-code":
            return {"status": "invalid_request"}
    except (KeyError, AttributeError, TypeError, ValueError, OSError, RuntimeError):
        return {"status": "invalid_request"}
    action = request["action"]
    if action == "rename":
        if request.get("mode") not in ("explicit", "automatic") or not valid_title(request.get("title")) or not isinstance(request.get("expected_title"), str):
            return {"status": "invalid_request"}
        if request["title"] != request["title"].strip():
            return {"status": "invalid_request"}
        if request["mode"] == "automatic" and (request.get("source") != "startup" or request.get("first_turn") is not True):
            return {"status": "invalid_request", "reason": "automatic_requires_first_startup_turn"}
    if action == "history":
        offset, limit = request.get("offset", 0), request.get("limit", 4)
        if type(offset) is not int or not 0 <= offset <= 100000 or type(limit) is not int or not 1 <= limit <= 20:
            return {"status": "invalid_request"}
    if sdk is None:
        try:
            sdk = import_module("claude_agent_sdk")
        except ImportError:
            return {"status": "unavailable", "reason": "sdk_missing"}
        except Exception:
            return {"status": "unavailable", "reason": "sdk_import_failed"}
    required = ["get_session_info"]
    if action != "inspect":
        required.append("get_session_messages" if action == "history" else "rename_session")
    if any(not callable(getattr(sdk, name, None)) for name in required):
        return {"status": "unavailable", "reason": "sdk_function_missing"}
    try:
        state = metadata(sdk.get_session_info(session_id, directory=str(directory)), session_id, directory)
    except Exception:
        return {"status": "error", "reason": "inspect_failed"}
    if state["status"] != "ok" or action == "inspect":
        return state
    if action == "history":
        return history(sdk, state, session_id, directory, offset, limit)
    if request["mode"] == "automatic" and state["custom_title"] is not None:
        return {**state, "status": "skipped", "reason": "custom_title_exists", "write_attempted": False}
    if request["mode"] == "automatic" and state["created_at"] is None:
        return {**state, "status": "skipped", "reason": "creation_time_missing"}
    if state["summary"] != request["expected_title"]:
        return {**state, "status": "conflict", "reason": "expected_title_mismatch", "write_attempted": False}
    if state["custom_title"] == request["title"]:
        return {**state, "status": "verified", "write_attempted": False}
    write_succeeded = False
    try:
        sdk.rename_session(session_id, request["title"], directory=str(directory))
        write_succeeded = True
    except Exception:
        pass  # A write can succeed before its response fails; only readback can verify it.
    try:
        after = metadata(sdk.get_session_info(session_id, directory=str(directory)), session_id, directory)
    except Exception:
        return {"status": "unverified", "reason": "readback_failed", "write_attempted": True, "write_succeeded": write_succeeded}
    if after["status"] != "ok":
        return {"status": "unverified", "reason": "readback_identity_unverified", "write_attempted": True, "write_succeeded": write_succeeded}
    return {
        **after, "status": "verified" if after["custom_title"] == request["title"] else "unverified",
        "write_attempted": True, "write_succeeded": write_succeeded,
    }


def history(sdk, state, session_id, directory, offset, limit):
    try:
        page = sdk.get_session_messages(session_id, directory=str(directory), offset=offset, limit=limit + 1)
        if not isinstance(page, list):
            return {"status": "error", "reason": "invalid_history"}
        if any(str(UUID(item.session_id)) != session_id for item in page):
            return {"status": "identity_mismatch"}
        messages = []
        for item in page[:limit]:
            if item.type not in ("user", "assistant") or getattr(item, "parent_tool_use_id", None) is not None or getattr(item, "parent_agent_id", None) is not None:
                continue
            if not isinstance(item.message, dict) or item.message.get("role", item.type) != item.type:
                continue
            content = item.message.get("content", [])
            if not isinstance(content, (str, list)):
                continue
            text = content if isinstance(content, str) else "\n".join(
                block["text"] for block in content
                if isinstance(block, dict) and block.get("type") == "text" and isinstance(block.get("text"), str)
            )
            if text:
                messages.append({"role": item.type, "text": text[:4000], "truncated": len(text) > 4000})
        return {
            **state, "messages": messages, "offset": offset, "limit": limit,
            "next_offset": offset + limit if len(page) > limit else None,
        }
    except Exception:
        return {"status": "error", "reason": "history_failed"}


def main():
    try:
        raw = sys.stdin.read(65537)
        request = json.loads(raw) if len(raw) <= 65536 else None
        response = handle_request(request)
    except (ValueError, OSError, UnicodeError, RecursionError):
        response = {"status": "invalid_request", "write_attempted": False, "write_succeeded": False}
    print(json.dumps(response, ensure_ascii=True, allow_nan=False))


if __name__ == "__main__":
    main()
