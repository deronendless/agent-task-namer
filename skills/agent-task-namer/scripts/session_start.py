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
    if client == "codex" and source == "startup":
        context = (
            f"STARTUP/root: Before the first substantive reply, read {skill} and follow its "
            "current-task workflow and automatic naming eligibility rules. "
            f"Trusted session_id={session_id}; source=startup. "
            "This Hook authorizes one automatic current-task title metadata update if those guards pass. "
            "Use read_thread, set_thread_title (omit threadId), then read_thread to verify. "
            "Root only; subagents ignore. Never rename other tasks. Then complete the user's request."
        )
    elif client == "codex":
        context = (
            f"LIFECYCLE/root: source={source}; current session_id={session_id}. "
            "This event does not authorize automatic naming. Preserve the current title and continue "
            f"the user's request. Read {skill} only if the user explicitly asks to name or diagnose "
            "this task, then follow its workflow. Never rename other tasks."
        )
    else:
        cwd = event.get("cwd")
        if not isinstance(cwd, str) or not Path(cwd).is_absolute() or any(ord(c) < 32 for c in cwd):
            return None
        identity = json.dumps({"session_id": session_id, "directory": cwd, "source": source})
        if source == "startup":
            context = (
                f"CLAUDE STARTUP/root: Before replying to the first substantive request, first read {skill} "
                "and run its Claude Code current-session workflow. "
                f"Trusted session identity: {identity}. "
                "This trusted startup Hook authorizes one automatic rename if the Skill guards pass: "
                "inspect with the official SDK bridge; rename once; inspect custom_title to verify. "
                "Preserve an existing custom title. If the bridge or reliable creation time is unavailable, "
                "offer a suggestion only. If the Skill cannot be read, skip naming. Root agent only; "
                "subagents must ignore this reminder. Never rename other sessions; then complete the user's request."
            )
        else:
            context = (
                f"CLAUDE LIFECYCLE/root: Trusted session identity: {identity}. "
                "This event does not authorize automatic naming. Preserve the current title and continue "
                f"the user's request. Read {skill} only if the user explicitly asks to name or diagnose "
                "this session, then follow its Claude Code workflow. Never rename other sessions."
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
