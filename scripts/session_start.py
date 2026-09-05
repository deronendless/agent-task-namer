#!/usr/bin/env python3
"""Remind the root agent to load the naming skill; never mutate task state."""

import argparse
import json
from pathlib import Path
import re
import sys


def hook_output(event, client="codex"):
    if client not in ("codex", "claude-code"):
        return None
    if not isinstance(event, dict) or event.get("hook_event_name") != "SessionStart":
        return None
    if event.get("agent_id") or event.get("parent_tool_use_id"):
        return None
    source = event.get("source")
    session_id = event.get("session_id")
    sources = ("startup", "resume", "clear", "compact")
    if source not in sources + (("fork",) if client == "claude-code" else ()):
        return None
    if not isinstance(session_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", session_id):
        return None
    skill = Path(__file__).resolve().parents[1] / "SKILL.md"
    if not skill.is_file():
        return None
    context = (
        f"Codex current task: session_id: {session_id}; session source: {source}. "
        "Use available official task tools; skip if they are unavailable. "
        "Do not bulk-rename old tasks unless the user requests it. "
    )
    if client == "claude-code":
        cwd = event.get("cwd")
        if not isinstance(cwd, str) or not Path(cwd).is_absolute() or any(ord(c) < 32 for c in cwd):
            return None
        context = (
            "Claude Code current session. "
            f"Trusted session identity: {json.dumps({'session_id': session_id, 'directory': cwd, 'source': source})}. "
            "Use the official SDK bridge; if unavailable, offer a suggestion only. "
            "Preserve existing custom titles. Do not rename other sessions. "
        )
    context += (
        "Naming reminder from the local agent-task-namer hook. Root agent only; subagents must ignore this reminder. "
        f"Read {skill} and follow its client workflow before naming; skip if it cannot be read. "
        "Name only a new task after its first substantive user request is clear, before the first final reply. "
        "Preserve existing correct or user-chosen titles. Respect preview-only requests. "
        "Resume, clear, compact, and fork do not authorize automatic renaming by themselves. "
        "Session events are not creation timestamps. Do not interrupt the user's main task or repeatedly rename it."
    )
    return {"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": context}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--client", choices=("codex", "claude-code"), default="codex")
    args = parser.parse_args()
    try:
        event = json.load(sys.stdin)
    except (ValueError, OSError, RecursionError):
        return
    output = hook_output(event, args.client)
    if output is not None:
        print(json.dumps(output))


if __name__ == "__main__":
    main()
