# Automatic naming: setup and maintenance

Read this only when the user requests installing, enabling, changing, or removing automatic naming. Routine renaming does not require hook configuration.

## How it works

Installing the skill alone provides explicit invocation and matching by its description. For Codex and Claude Code's `SessionStart` event, `scripts/session_start.py` emits `hookSpecificOutput.additionalContext` to remind the main agent to read this skill. It does not call a model, read conversation transcripts, rename tasks, or save state. No arguments retain the original Codex behavior; `--client claude-code` selects Claude Code. Unknown clients fail without emitting a reminder. Subagent events and identities are skipped; a custom main-agent `agent_type` alone is not a subagent identity.

`startup`, `resume`, `clear`, `compact`, and Claude's `fork` are session events only; they do not establish that a task is new or when it was created. Wait for the first substantive user request. Resume, clear, compact, and fork preserve existing titles unless the user explicitly requests a rename. The skill chooses the [client workflow](clients.md); other agents receive suggestions only.

## Codex configuration

The hook can be configured in `$CODEX_HOME/hooks.json` (usually `~/.codex/hooks.json`) or the corresponding `config.toml`. Inspect existing definitions before adding it, preserve other hooks, and avoid registering this script more than once. Hooks from multiple sources are merged for execution; do not install by overwriting the entire configuration file.

The example below shows the configuration structure. During installation, replace the path with the actual absolute path on the user's machine, use a verified Python 3 interpreter, and quote paths containing spaces correctly:

```json
{
  "hooks": {
    "SessionStart": [{
      "matcher": "^(startup|resume|clear|compact)$",
      "hooks": [{
        "type": "command",
        "command": "python3 /absolute/path/agent-task-namer/scripts/session_start.py",
        "timeout": 3,
        "additionalContextLimit": 600
      }]
    }]
  }
}
```

Unmanaged hooks must be reviewed and trusted by the user through `/hooks` in the Codex CLI. New or changed hook definitions will not run until trusted. Do not edit trust records, use trust-bypass arguments, or claim that saving configuration means activation succeeded. If hooks are disabled in the current environment, explain that state first and follow the user's choice about enabling them.

## Claude Code local CLI setup

Install this skill directory at `~/.claude/skills/agent-task-namer/`. Preserve any existing files and compare them before updating; do not overwrite external changes. Use `agent-task-namer` for the repository and skill directory, and `/agent-task-namer` for Claude invocation.

Only the Claude bridge needs the optional official SDK. Use Python 3.10+ in a virtual environment outside the skill and repository (Python 3.13 was selected for local verification):

```sh
python3.13 -m venv "$HOME/.local/share/agent-task-namer/venv"
"$HOME/.local/share/agent-task-namer/venv/bin/python" -m pip install -r "$HOME/.claude/skills/agent-task-namer/scripts/requirements-claude.txt"
```

Replace `python3.13` with your verified Python 3.10+ interpreter if needed. The requirements file pins the tested SDK. Codex and suggestion mode need no SDK. The bridge uses only local session helpers, never starts another model, and does not need an API key of its own. Do not install into system Python or bundle the virtual environment in the skill. For another virtual-environment location, use that interpreter explicitly when calling the bridge.

Check `claude --version` and the documented capabilities of the actual executable. If required skill identity substitution or session metadata is missing, follow the user's upgrade preference and the [official setup instructions](https://code.claude.com/docs/en/setup) for their existing installation channel. Test stable versions before changing claims of support; do not guess a minimum version from the SDK version.

First use a dedicated, reviewed test project and pass a settings file with `claude --settings /absolute/path/test-settings.json`. Review the workspace through Claude's normal trust flow. After testing, merge only the entry below into `~/.claude/settings.json`, preserving other settings and hooks. Replace the interpreter and script paths with verified absolute paths and quote paths with spaces:

```json
{
  "hooks": {
    "SessionStart": [{
      "matcher": "^(startup|resume|clear|compact|fork)$",
      "hooks": [{
        "type": "command",
        "command": "python3 /absolute/path/agent-task-namer/scripts/session_start.py --client claude-code",
        "timeout": 3
      }]
    }]
  }
}
```

Claude workspace trust and Codex hook trust are separate. Do not copy Codex's `additionalContextLimit` or edit trust records. Do not use noninteractive execution to bypass a pending trust decision. Saving configuration is not proof the reminder ran. The hook supplies the current session ID and directory; the main agent must still inspect that session through the bridge before naming. Existing custom titles are preserved in automatic mode.

If the SDK is missing, the ID is unexpanded or inconsistent, or the session is unreadable, use suggestion mode. A `conflict` requires a fresh read and reassessment; an unverified write requires a read before any targeted retry. Never fix these conditions by editing private session files. Claude Desktop, cloud sessions, and Claude batch/restore are outside this version's scope.

To disable, remove only this script's Claude hook entry. Keep unrelated hooks, the optional on-demand skill, user sessions, and Codex batch records. Roll back repository changes with a new revert commit and restore corresponding installed files; do not automatically downgrade the CLI or delete test sessions.

## Verification and migration

1. Run `python3 scripts/test_session_start.py` to verify event inputs, JSON output, and non-blocking behavior.
2. After the user trusts the hook, verify in a Codex client with task tools that the first response in a new task names it, ordinary follow-up conversation does not repeatedly rename it, subagents do not rename the parent task, and resuming an old task does not trigger batch renaming.
3. Remove duplicate naming instructions from the global `AGENTS.md` only after an actual trigger has been successfully verified and the user has requested migration. Preserve other personalization instructions. Automatic triggering still depends on the host, hook trust, and available title-writing tools.

To disable automatic naming, disable this hook in `/hooks` or remove only the configuration entry for this script. The skill remains available on demand. No scheduled tasks, background services, or direct changes to the Codex database are needed.

For Claude, run `python3 scripts/test_claude_session.py` with the mocked SDK, then use dedicated real sessions to verify loading, trusted identity, explicit naming, first-turn hook naming, continuation/resume/custom-title preservation, and persistence after reopening. Record actual versions and outcomes in [validation](validation.md); mark only observed capabilities as verified. Do not trial writes in daily sessions.

Official references: [Codex Skills](https://learn.chatgpt.com/docs/build-skills), [Codex Hooks](https://learn.chatgpt.com/docs/hooks), [Claude Skills](https://code.claude.com/docs/en/skills), [Claude Hooks](https://code.claude.com/docs/en/hooks).
