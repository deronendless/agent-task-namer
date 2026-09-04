# Automatic naming: setup and maintenance

Read this only when the user requests installing, enabling, changing, or removing automatic naming. Routine renaming does not require hook configuration.

## How it works

Installing the skill alone provides explicit invocation and matching by its description. For Codex's `SessionStart` event, `scripts/session_start.py` emits `hookSpecificOutput.additionalContext` to remind the main agent to read this skill. It does not call a model, read conversation transcripts, rename tasks, or save state.

`startup`, `resume`, `clear`, and `compact` are session events only; they do not establish that a task is new or when it was created. The skill decides whether naming is needed and performs it through the official tools available in the current environment.

## Local configuration

The hook can be configured in `$CODEX_HOME/hooks.json` (usually `~/.codex/hooks.json`) or the corresponding `config.toml`. Inspect existing definitions before adding it, preserve other hooks, and avoid registering this script more than once. Hooks from multiple sources are merged for execution; do not install by overwriting the entire configuration file.

The example below shows the configuration structure. During installation, replace the path with the actual absolute path on the user's machine, use a verified Python 3 interpreter, and quote paths containing spaces correctly:

```json
{
  "hooks": {
    "SessionStart": [{
      "matcher": "^(startup|resume|clear|compact)$",
      "hooks": [{
        "type": "command",
        "command": "python3 /absolute/path/codex-task-namer/scripts/session_start.py",
        "timeout": 3,
        "additionalContextLimit": 600
      }]
    }]
  }
}
```

Unmanaged hooks must be reviewed and trusted by the user through `/hooks` in the Codex CLI. New or changed hook definitions will not run until trusted. Do not edit trust records, use trust-bypass arguments, or claim that saving configuration means activation succeeded. If hooks are disabled in the current environment, explain that state first and follow the user's choice about enabling them.

## Verification and migration

1. Run `python3 scripts/test_session_start.py` to verify event inputs, JSON output, and non-blocking behavior.
2. After the user trusts the hook, verify in a Codex client with task tools that the first response in a new task names it, ordinary follow-up conversation does not repeatedly rename it, subagents do not rename the parent task, and resuming an old task does not trigger batch renaming.
3. Remove duplicate naming instructions from the global `AGENTS.md` only after an actual trigger has been successfully verified and the user has requested migration. Preserve other personalization instructions. Automatic triggering still depends on the host, hook trust, and available title-writing tools.

To disable automatic naming, disable this hook in `/hooks` or remove only the configuration entry for this script. The skill remains available on demand. No scheduled tasks, background services, or direct changes to the Codex database are needed.

Official references: [Skills](https://learn.chatgpt.com/docs/build-skills), [Hooks](https://learn.chatgpt.com/docs/hooks).
