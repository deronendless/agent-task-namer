# Automatic naming: setup and maintenance

Read this only when the user requests installing, enabling, changing, or removing automatic naming. Routine renaming does not require hook configuration.

## How it works

Installing the skill alone provides explicit invocation and matching by its description. For Codex and Claude Code's `SessionStart` event, `scripts/session_start.py` emits `hookSpecificOutput.additionalContext` to remind the main agent to read this skill. It does not call a model, read conversation transcripts, rename tasks, or save state. No arguments retain the original Codex behavior; `--client claude-code` selects Claude Code. Unknown clients fail without emitting a reminder. Subagent events and identities are skipped; a custom main-agent `agent_type` alone is not a subagent identity.

`startup`, `resume`, `clear`, `compact`, and Claude's `fork` are session events only; they do not establish that a task is new or when it was created. Wait for the first substantive user request. Resume, clear, compact, and fork preserve existing titles unless the user explicitly requests a rename. The skill chooses the [client workflow](clients.md); other agents receive suggestions only.

## Codex plugin installation

The repository is also a native Codex plugin source: `.codex-plugin/plugin.json` declares the package, `skills/agent-task-namer/SKILL.md` is the plugin skill entry, and `hooks/hooks.json` bundles the `SessionStart` hook. Use the [standard plugin distribution workflow](https://developers.openai.com/plugins/build/plugins#how-local-marketplaces-work) to expose the repository through a Codex marketplace and install it through the client. This repository has not yet been published as a marketplace listing; do not present a source URL as an existing one-click installation link.

Codex discovers the enabled plugin's bundled hook automatically. Users do not need to add it to their own `hooks.json` or `config.toml`. The local host must provide `python3` on `PATH`; the plugin does not bundle a Python runtime. Plugin commands resolve packaged files through `PLUGIN_ROOT`, which Codex supplies for the installed plugin; do not replace it with an author's machine-specific path.

Installation does not grant hook trust. In the desktop app's plugin detail page, review the hook and choose **Trust all** to trust this plugin's pending hooks in one operation. **Review** opens the hook details. The CLI equivalent is `/hooks`. After the current definition is trusted and enabled, subsequent new tasks require no per-session setup. A changed definition may require review again. See the official [plugin hook trust rules](https://developers.openai.com/plugins/build/plugins#bundled-mcp-servers-and-lifecycle-hooks).

When migrating from a standalone Skill hook, inspect the active hook sources and disable or remove only the previous `agent-task-namer` naming-hook entry before enabling the plugin hook. Codex merges hooks from different sources, so leaving both active produces duplicate reminders. Preserve unrelated hooks and settings. Do not register the plugin hook again in user configuration.

To disable automatic naming while retaining on-demand naming, disable this plugin's naming hook in the app's Hooks settings or CLI `/hooks`. Disabling the entire plugin also removes its skill from use. Verify activation in a dedicated new task after the normal trust flow; installation or saved configuration alone is not verification.

## Codex standalone Skill configuration

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

Unmanaged hooks must be reviewed and trusted by the user through the desktop app's Hooks settings or `/hooks` in the Codex CLI. New or changed hook definitions will not run until trusted. Do not edit trust records, use trust-bypass arguments, or claim that saving configuration means activation succeeded. These rules apply to both standalone and plugin-bundled hooks. If hooks are disabled in the current environment, explain that state first and follow the user's choice about enabling them.

To disable automatic naming, disable this hook in the app's Hooks settings or CLI `/hooks`, or remove only its configuration entry. The skill remains available on demand. No scheduled tasks, background services, or direct changes to the Codex database are needed.

## Claude Code local CLI setup

Install this skill directory at `~/.claude/skills/agent-task-namer/`. Preserve any existing files and compare them before updating; do not overwrite external changes. Use `agent-task-namer` for the repository and skill directory, and `/agent-task-namer` for Claude invocation.

Only the Claude bridge needs the optional official SDK. Use a Python 3.10+ interpreter to create a virtual environment outside the skill and repository:

```sh
python3 -m venv "$HOME/.local/share/agent-task-namer/venv"
"$HOME/.local/share/agent-task-namer/venv/bin/python" -m pip install -r "$HOME/.claude/skills/agent-task-namer/scripts/requirements-claude.txt"
```

Replace `python3` with the path to a Python 3.10+ interpreter if needed. The requirements file pins the SDK version. Codex and suggestion mode need no SDK. The bridge uses only local session helpers, never starts another model, and does not need an API key of its own. Do not install into system Python or bundle the virtual environment in the skill. For another virtual-environment location, use that interpreter explicitly when calling the bridge.

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

To disable, remove only this script's Claude hook entry. Keep unrelated hooks, the optional on-demand skill, user sessions, and Codex batch records.

## Verification

Follow the [acceptance checks](validation.md) for script tests and activation checks in dedicated tasks or sessions. Keep environment details and run results outside the repository; mark only observed capabilities as verified.

Official references: [Codex Skills](https://learn.chatgpt.com/docs/build-skills), [Codex Hooks](https://learn.chatgpt.com/docs/hooks), [Claude Skills](https://code.claude.com/docs/en/skills), [Claude Hooks](https://code.claude.com/docs/en/hooks).
