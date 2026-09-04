# Agent Task Namer

[简体中文](README.zh-CN.md)

Give agent tasks consistent, easy-to-find titles. Works with Codex, Claude Code local CLI, and title suggestions in other agents.

```text
🐛 Fix | 260904 | Login callback failure
📝 Docs | 260904 | Atlas deployment guide
⚡ 优化 | 260904 | 登录页面布局
```

Each title follows the language of that task's main request. Dates stay tied to task creation, using Beijing time by default.

| Client | Rename current task | Optional automatic naming | Batch and restore |
|---|---|---|---|
| Codex (official task tools required) | Supported | Supported | Supported |
| Claude Code local CLI (optional SDK required) | Local title read/write verified | Pending end-to-end verification | Not included |
| Other agents that can read skills | Suggestions only | Not included | Not included |

See [validation](references/validation.md) for tested environments and verification status.

## 1. Install

Send this to your agent:

```text
Install the codex-task-namer skill from https://github.com/deronendless/codex-task-namer
```

For Claude Code, install at `~/.claude/skills/codex-task-namer/` and [set up the optional SDK](references/automatic.md#claude-code-local-cli-setup) to rename sessions. Other agents can use their skill loader or read this repository’s `SKILL.md`. The repository and skill identifier remain `codex-task-namer`.

## 2. Use

**Codex: rename the current task**

```text
$codex-task-namer Rename this task using the standard format.
```

**Claude Code: rename the current session**

```text
/codex-task-namer Rename this session using the standard format.
```

**Other agents: suggest a title**

```text
Read codex-task-namer/SKILL.md and suggest a title based on this task’s main request.
```

Without a reliable creation time, you get a type and topic draft instead of a guessed date.

**Codex: preview project titles**

```text
$codex-task-namer Preview new titles for the tasks in this project. Do not rename them yet.
```

**Codex: organize a project's tasks**

```text
$codex-task-namer Organize the titles of all tasks in this project.
```

Accurate, compliant titles and titles you explicitly chose are preserved. To change the language, just ask: “Translate this task's title into English, keeping the format.”

## Optional: name new tasks automatically

Send this to Codex or Claude Code:

```text
Enable automatic naming for new tasks with codex-task-namer.
```

This requires separate setup and client support; installation alone does not enable it. Follow your client's normal configuration review and trust flow. See [setup details](references/automatic.md).

---

[Detailed rules](SKILL.md) · [Batch rename and restore](references/batch.md) · [Validation](references/validation.md) · [MIT License](LICENSE)

Community skill; not an official OpenAI or Anthropic product.
