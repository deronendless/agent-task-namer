# Codex Task Namer

[简体中文](README.zh-CN.md)

A Codex skill that gives tasks consistent, language-aware titles:

```text
emoji Type | YYMMDD | Topic

🐛 Fix | 260904 | Login callback failure
📝 Docs | 260904 | Atlas deployment guide
⚡ 优化 | 260904 | 登录页面布局
```

## What it does

- Names the current task, previews proposed titles, or organizes an explicitly requested set of project tasks.
- Uses the language of each task's substantive user request for both the category and topic. Code, logs, quotations, and short replies do not determine the language.
- Keeps the original creation date across days and years. The default timezone is **Asia/Shanghai**, regardless of title language; an explicit user timezone takes precedence.
- Preserves exact user-chosen titles and accurate, compliant titles. Continuing in another language does not translate an existing title unless requested.
- Records batch changes locally so interrupted runs can resume and recorded changes can be restored on request, with checks for intervening edits.

Categories are ✨ Feature, 🎨 Design, 🐛 Fix, ⚡ Optimize, 🚀 Release, 🔍 Explore, 📝 Docs, and 🔬 Research. Chinese has fixed labels; other languages use natural translations of the same eight categories with the same emoji.

## Requirements

Use a Codex environment that supports skills and exposes official task-reading and title-writing tools, such as `read_thread` and `set_thread_title`.

**This skill does not provide those tools.** If task identity, the necessary tools, or a reliable creation time cannot be established, it preserves the title. A user-specified exact title does not require creation-time inference. It never writes directly to Codex's database.

Python 3 is needed only for the optional hook and its tests. The Python files use the standard library; no API key or Python package installation is required.

## Install

Clone this repository into your personal skills directory:

```sh
task_skill_dir="${CODEX_HOME:-$HOME/.codex}/skills/codex-task-namer"
mkdir -p "$(dirname "$task_skill_dir")"
git clone https://github.com/deronendless/codex-task-namer.git "$task_skill_dir"
```

If that directory already exists, review the existing installation before replacing anything. The skill is available on the next turn in a client that discovers this skills directory.

## Use

Ask Codex, for example:

```text
$codex-task-namer Rename this task using the standard format.
$codex-task-namer Preview new titles for the tasks in this project.
$codex-task-namer Organize the titles of all tasks in this project.
$codex-task-namer Translate this task's title into English, keeping the format.
$codex-task-namer Restore the changes from the batch record I provide.
```

Batch language is determined separately for each task unless you explicitly request one language for the whole batch. Bulk renaming requires an explicit request; a new-task reminder does not authorize it.

## Optional automatic naming

Installing the skill enables explicit invocation and skill matching; it does **not** guarantee automatic naming on every new chat.

The included `SessionStart` hook emits a reminder for the main agent to load the skill. It does not call a model, read conversation transcripts, or rename tasks itself. Automatic naming depends on the host's hook support, user trust, and available task tools. `startup`, `resume`, `clear`, and `compact` are lifecycle events, not creation timestamps.

Ask Codex to follow [the hook setup guide](references/automatic.md) to merge the hook into your existing configuration. Set the actual interpreter and script paths, and review and trust the hook through the host's supported flow. Installing this repository does not alter hook configuration or trust records.

## Validation and maintenance

Run the hook protocol tests from the repository root:

```sh
python3 scripts/test_session_start.py
```

These tests do not access live tasks and do not prove model naming decisions. [Behavioral validation cases](references/validation.md) cover dates, languages, title preservation, batch scope, interruption, and restoration.

- [SKILL.md](SKILL.md): naming rules and current-task workflow.
- [Batch workflow](references/batch.md): scope checks, local records, resume, and restore.
- [Hook setup](references/automatic.md): optional installation and verification.

The core instructions and detailed references are currently written in Chinese; generated titles follow the user's request language. Batch records remain outside the skill directory and should not be committed. Fresh reads reduce accidental overwrites but do not provide an atomic lock against concurrent title changes.

## License

[MIT](LICENSE). This is a community skill and is not an official OpenAI product.
