# Codex Task Namer

[简体中文](README.zh-CN.md)

Give your Codex tasks consistent titles that are easy to find in the sidebar.

```text
🐛 Fix | 260904 | Login callback failure
📝 Docs | 260904 | Atlas deployment guide
⚡ 优化 | 260904 | 登录页面布局
```

Each title follows the language of that task's main request. Dates stay tied to task creation, using Beijing time by default.

## 1. Install

Send this to Codex:

```text
Install the codex-task-namer skill from https://github.com/deronendless/codex-task-namer
```

After installation, use it from the next turn. Your Codex client must support reading and renaming tasks.

## 2. Use

**Rename the current task:**

```text
$codex-task-namer Rename this task using the standard format.
```

**Preview titles before changing them:**

```text
$codex-task-namer Preview new titles for the tasks in this project. Do not rename them yet.
```

**Organize a project's tasks:**

```text
$codex-task-namer Organize the titles of all tasks in this project.
```

Accurate, compliant titles and titles you explicitly chose are preserved. To change the language, just ask: “Translate this task's title into English, keeping the format.”

## Optional: name new tasks automatically

Send this to Codex:

```text
Enable automatic naming for new tasks with codex-task-namer.
```

This requires separate setup and client support; installation alone does not enable it. Follow Codex's instructions to review and trust the configuration. See [setup details](references/automatic.md).

---

[Detailed rules](SKILL.md) · [Batch rename and restore](references/batch.md) · [Validation](references/validation.md) · [MIT License](LICENSE)

Community skill; not an official OpenAI product.
