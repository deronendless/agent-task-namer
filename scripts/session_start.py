#!/usr/bin/env python3
"""Remind the root agent to load the naming skill; never mutate task state."""

import json
from pathlib import Path
import re
import sys


def hook_output(event):
    if not isinstance(event, dict) or event.get("hook_event_name") != "SessionStart":
        return None
    source = event.get("source")
    session_id = event.get("session_id")
    if source not in ("startup", "resume", "clear", "compact"):
        return None
    if not isinstance(session_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", session_id):
        return None
    skill = Path(__file__).resolve().parents[1] / "SKILL.md"
    if not skill.is_file():
        return None
    context = (
        "Codex task naming reminder from the local codex-task-namer hook. "
        "Root agent only; subagents must ignore this reminder. "
        f"Current session_id: {session_id}; session source: {source}. "
        f"Read {skill} and apply its current-task mode when applicable. "
        "For a new task, name it once its actual topic is clear, before the first final reply. "
        "Use available official task tools; skip if they are unavailable. "
        "Session startup/resume/clear/compact does not establish task creation time. "
        "Preserve existing correct or user-chosen titles; do not bulk-rename old tasks "
        "unless the user requests it. Respect preview-only requests. "
        "Do not interrupt the user's main task or repeatedly rename it."
    )
    return {"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": context}}


def main():
    try:
        event = json.load(sys.stdin)
    except (ValueError, OSError):
        return
    output = hook_output(event)
    if output is not None:
        print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    main()
