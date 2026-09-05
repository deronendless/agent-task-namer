# Agent Task Namer

[简体中文](README.zh-CN.md)

Give agent tasks consistent, easy-to-find titles. Works with Codex, Claude Code local CLI, and title suggestions in other agents.

![Task titles before and after naming with type, creation date, and topic](assets/readme/before-after-en.png)

*Illustrative comparison of the same tasks using consistent type, creation date, and topic.*

```text
🐛 Fix | 260904 | Login callback failure
📝 Docs | 260904 | Atlas deployment guide
⚡ 优化 | 260904 | 登录页面布局
```

Each title follows the language of that task's main request. Dates stay tied to task creation, using Beijing time by default.

| Client | Rename current task | Optional automatic naming | Batch and restore |
|---|---|---|---|
| Codex (official task tools required) | Supported | Supported | Supported |
| Claude Code local CLI (optional SDK required) | Experimental | Experimental | Not included |
| Other agents that can read skills | Suggestions only | Not included | Not included |

Claude Code support is experimental; end-to-end validation is still pending.

## 1. Install

For Codex automatic naming, this repository also provides a plugin containing the skill and its startup hook. The repository can be used as a plugin source through the [standard marketplace distribution workflow](https://developers.openai.com/plugins/build/plugins#how-local-marketplaces-work). No marketplace listing has been published yet.

The standalone Skill remains supported. Send this to your agent:

```text
Install the agent-task-namer skill from https://github.com/deronendless/agent-task-namer/tree/main/skills/agent-task-namer
```

For Claude Code, copy the repository's `skills/agent-task-namer/` directory to `~/.claude/skills/agent-task-namer/` and [set up the optional SDK](skills/agent-task-namer/references/automatic.md#claude-code-local-cli-setup) to rename sessions. Other agents can use their skill loader or read [skills/agent-task-namer/SKILL.md](skills/agent-task-namer/SKILL.md). The repository, skill directory, and invocation identifier are `agent-task-namer`.

## 2. Use

**Codex: rename the current task**

```text
$agent-task-namer Rename this task using the standard format.
```

**Claude Code: rename the current session**

```text
/agent-task-namer Rename this session using the standard format.
```

**Other agents: suggest a title**

```text
Read skills/agent-task-namer/SKILL.md in the repository and suggest a title based on this task’s main request.
```

Without a reliable creation time, you get a type and topic draft instead of a guessed date.

For Codex project tasks, ask `$agent-task-namer` to “Preview new titles without applying them” or “Organize the titles of all tasks in this project.”

Accurate, compliant titles and titles you explicitly chose are preserved. To change the language, just ask: “Translate this task's title into English, keeping the format.”

## Optional: name new tasks automatically

**Codex plugin:** installation discovers the bundled hook without editing `hooks.json`. In the plugin's detail page, review its hook and choose **Trust all** once. Subsequent new tasks need no setup; changed hook definitions may need review again. Installing the plugin alone does not grant hook trust.

**Standalone Skill or Claude Code:** send this to your agent:

```text
Enable automatic naming for new tasks with agent-task-namer.
```

The standalone Skill requires separate hook setup and the client's normal trust flow. When switching to the Codex plugin, remove the old naming hook to avoid duplicate reminders. See [setup and migration details](skills/agent-task-namer/references/automatic.md).

## Repository layout

```text
.codex-plugin/           Plugin manifest
hooks/                  Codex plugin startup hook configuration
skills/agent-task-namer/ Standalone Skill, scripts, and reference documents
assets/readme/          README illustrations and source artwork
```

---

[Detailed rules](skills/agent-task-namer/SKILL.md) · [Batch rename and restore](skills/agent-task-namer/references/batch.md) · [MIT License](LICENSE)

Community skill; not an official OpenAI or Anthropic product.
