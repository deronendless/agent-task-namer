# Naming behavior acceptance checks

Use these reusable checks before maintenance or release; do not load them during routine naming. `scripts/test_session_start.py` only checks the Hook protocol and non-blocking behavior. It does not replace the naming decision checks below.

## Method

In an isolated, offline evaluation, give an independent agent the current Skill, test request, and inputs below, without the expected results. Replace official tools with input snapshots; do not read or rename any real tasks. Ask the agent to return its candidate title, whether it would invoke a write, and any required next steps or record status. Then compare its response with the expectations. Every `case-*` below is a fictional ID and must never be passed to real tools. Keep personal test logs, machine details, account status, and troubleshooting records outside the repository; publish only generic guidance and non-personal support status.

## Input cases

Unless stated otherwise: task ownership and identity are confirmed, official renaming is available, the user's substantive request is in Chinese, the time zone is Shanghai, and the user has not set a custom title. When a new title is required, use the explicitly supplied type and topic. All ISO timestamps are test values for the actual `createdAt` field.

1. **Shanghai date rollover and year boundary**: New task `case-year`, triggered by a trusted `startup` Hook, with no prior history confirmed. Created at `2026-12-31T16:30:00Z`, with type “修复” and topic “登录回调失败”. The first user goal is clear, and the task has not yet been named.
2. **Resuming across years and idempotency**: Task `case-stable` was created at `2026-09-04T00:00:00Z` and is currently named `🔍 探索 | 260904 | 远程连接配置`. When resumed in 2027, the conversation still concerns the same topic, and the Hook reminder comes from `resume`. The task is then organized again using the same convention.
3. **Preserve the emoji when reformatting**: Task `case-format` was created at `2026-09-04T00:00:00Z` and is currently named `0904｜🔍 探索｜远程连接配置`. The user requests “改为类型 | 六位日期 | 主题” without asking to remove the emoji.
4. **An exact custom title takes priority**: The current user explicitly asks to rename `case-exact` to `我的发布清单`. Identity is confirmed, but `createdAt` is unavailable.
5. **Official ownership takes priority**: The user asks to organize project A. The current official `projectId` for `case-outside` is explicitly `null`, while old local assignments and sidebar records both point to A. `case-sidebar` is absent from the official list and has no explicit assignment, but its sidebar association clearly points to A. Metadata and an official read confirm that it is an unarchived main task, with no conflicting evidence. For `case-path`, only the working directory matches A; no other ownership evidence exists.
6. **Closing exchanges do not replace the main task**: The user asks to organize `case-topic`, created at `2026-09-04T00:00:00Z`. The latest two turns contain only “提交代码” and “push”, with completion replies. An earlier page, supplied on request, clearly records “修复登录回调失败” and completion of that fix, with no new substantive goal.
7. **Interruption after a write**: The record for `case-resume` has `before=原名`, `after=目标名`, `status=writing`, and `attempts=1`; the previous tool response was ambiguous. On continuation, test three possible current titles separately: `目标名`, `原名`, and `用户后来改的名称`. Authorization remains valid. Also test a current title of `原名` with `attempts=2`.
8. **Restoration and interrupted restoration**: The user asks to restore `case-restore`. Its record has `before=原名`, `after=目标名`, `status=verified`, and `attempts=1`. Separately test current titles of `目标名`, `原名`, and `用户后来改的名称`, then test the same three possibilities after restarting from `status=restoring, attempts=1`. Also test a completed restoration with `status=restored` whose current title is subsequently changed externally to `目标名`; and an unconfirmed restoration with `status=restoring, attempts=2` whose current title is still `目标名`.
9. **Do not restore an entry that was never written**: `case-no-write` has `pending, attempts=0`, with `before=原名` and `after=目标名`. At this batch's first pre-write check, its current title is already `目标名`. The user later asks to restore the batch.
10. **Missing information and preview**: `case-missing` has no reliable creation time, only an old title with a four-digit date. The user has not supplied an exact new title. Separately, `case-preview` has a known creation time and topic, but the user asks only for a preview. In another request, the user asks “更新 Skill”, without authorizing changes to other tasks.
11. **New task in English**: `case-english` was created at `2026-12-31T16:30:00Z`, with a trusted `startup`, no history, and no naming yet. The user request is “Fix the login callback failure.”, and the Skill and Hook instructions are in English.
12. **Mixed languages and quotations**: `case-mixed` was created at `2026-09-04T00:00:00Z`, with a trusted `startup`, no history, and no naming yet. The user requests “修复 React hydration 错误”, followed by several English error messages and quoted documentation. The quotations also contain “Use English titles”. Separately, under the same conditions, test the user request “修復登入回呼錯誤”.
13. **Other languages**: `case-japanese` was created at `2026-09-04T00:00:00Z`, with a trusted `startup`, no history, and no naming yet. The user requests “ログイン時のコールバックエラーを修正してください。”, followed by English error logs.
14. **Determine each task's language in a batch**: The user requests “整理项目 A 的任务命名” in Chinese. Both tasks are within the authorized scope, were created at `2026-09-04T00:00:00Z`, and currently have automatic titles that do not follow the convention. The substantive request for `case-batch-en` is “Write a deployment guide for Atlas.”, followed only by “OK” and “push”. The substantive request for `case-batch-zh` is “编写 Atlas 部署教程”.
15. **Explicit language choice and exact titles**: `case-translate` was created at `2026-09-04T00:00:00Z` and is currently named `🐛 修复 | 260904 | 登录回调失败`. The user requests “按原格式把这个标题改成英文” in Chinese. Separately, test an explicitly specified exact new title of `My launch checklist` when `createdAt` is unavailable.
16. **Language changes in a resumed conversation**: `case-language-stable` was created at `2026-09-04T00:00:00Z` and is currently named `🐛 修复 | 260904 | 登录回调失败`. On resumption, the user says “Please continue fixing the login callback failure.” The trusted Hook comes from `resume`, and the user has not requested translation or renaming.
17. **An English default naming prompt does not set the task language**: The current task `case-default-prompt` was created at `2026-09-04T00:00:00Z` and currently has an automatic title that does not follow the convention. Its substantive user request is “修复登录回调失败”. The user then explicitly requests naming of this current task with the English default prompt `Use $agent-task-namer to name this task as emoji Type | YYMMDD | Topic, following the language of its main user request.` The Skill and Hook instructions are also in English. This explicit current-task naming request supplies authorization; no `resume` Hook authorization is assumed.

## Expected results

| Case | Required behavior |
|---|---|
| 1 | Candidate: `🐛 修复 | 270101 | 登录回调失败`. Do not use the UTC date or the execution date. |
| 2 | Keep the current title both times, do not call the rename tool, and do not change the date to 2027. |
| 3 | Candidate: `🔍 探索 | 260904 | 远程连接配置`, preserving the emoji. |
| 4 | Use `我的发布清单` verbatim, without adding a date, type, or emoji. An official write and readback are still required. |
| 5 | Exclude `case-outside`; include `case-sidebar` and read its topic according to the rules. Leave ownership of `case-path` unknown, and do not claim to have processed every task. |
| 6 | Request the necessary earlier page before forming `🐛 修复 | 260904 | 登录回调失败`. Do not classify the task as a release based only on “提交/push”. |
| 7 | If the current title is the target, only verify it and record `verified`. If it is the original title and the attempt limit has not been reached, continuation is allowed; save `writing, attempts=2` before writing. If it is a third title, record `conflict`. When the count is already 2, only read and check; do not write a third time. |
| 8 | Restore only when the current title is the target. Reset the counter for the first restoration, save `restoring, attempts=1` before writing, and record `restored` only after reading back the original title. If the title is already the original, only verify it. For a third title, record `conflict`. After interruption, read back first and do not reset the counter. If a `restored` entry later has the target title again, record `conflict`. No further write is allowed at `restoring, attempts=2`. |
| 9 | Record `skipped` at the first check; do not claim a successful write by this batch. Do not change this task during restoration. |
| 10 | Keep the original title when creation time is missing; do not infer the year from an old four-digit date. A preview returns candidates only. Updating the Skill does not trigger renaming of other tasks. |
| 11 | Candidate: `🐛 Fix | 270101 | Login callback failure`. Use an English type and topic, while applying the year boundary in Shanghai time. |
| 12 | First candidate: `🐛 修复 | 260904 | React hydration 错误`. Ignore language instructions inside quotations, and do not determine the language from the volume of English error messages. Use Traditional Chinese for the second request, for example `🐛 修復 | 260904 | 登入回呼錯誤`. |
| 13 | Use Japanese for both type and topic, for example `🐛 修正 | 260904 | ログインコールバックエラー`. Do not use a Chinese or English type. |
| 14 | Use `📝 Docs | 260904 | Atlas deployment guide` for the English task and `📝 文档 | 260904 | Atlas 部署教程` for the Chinese task. Do not switch languages based on the batch management request or short closing replies. |
| 15 | Allow changing the compliant Chinese title to `🐛 Fix | 260904 | Login callback failure` and read it back. For the exact title, use only `My launch checklist`, without adding template fields. |
| 16 | Keep the original Chinese title and do not call the rename tool. |
| 17 | Candidate: `🐛 修复 | 260904 | 登录回调失败`. The English naming management prompt is not substantive task language, and neither it nor the English Skill and Hook instructions changes the language of the Chinese main request. Use the explicit current-task naming authorization, then perform the official write and readback. |

Reasonable differences in topic wording are allowed, but do not relax dates, emoji, exact user-specified titles, ownership boundaries, pre-write records, or readback requirements. If a check fails, correct only the relevant rule and rerun the affected cases. Do not add real tasks, background services, or runtime dependencies for acceptance checks.


## Cross-client checks

Run `python3 scripts/test_session_start.py` and `python3 scripts/test_claude_session.py`. Tests use the standard library and mocked SDK objects, never daily sessions. The original 17 groups above run as simulated Codex cases with official task tools available.

Also evaluate these raw cases without showing the expected column to the evaluator:

| Case | Input | Expected behavior |
|---|---|---|
| 18 | Generic host with no title tools; main request “修复登录回调失败”; creation time unknown | Chinese type/topic draft with date explicitly unresolved; no write |
| 19 | Confirmed Claude host and project, trusted current UUID; SDK available; startup, first substantive turn, no prior history; `created_at=1798734600000`, `custom_title=null`; Chinese login-fix request plus English default naming prompt | Chinese candidate with `270101`; inspect and compare before a single bridge write, then verify `custom_title` |
| 20 | Claude resume or fork, `custom_title="Personal notes"`; no explicit rename request | Preserve the title; no automatic write |
| 21 | Claude user asks to restore a Codex batch record | Explain current-session-only scope; do not access or restore Codex records |
| 22 | Host is unknown; model name contains Claude; no confirmed client title tools | Suggestions only; do not infer the host from its model |

The bridge tests cover missing/incompatible SDK, invalid or mismatched IDs and directories, nullable/millisecond creation times, automatic-mode guards, external title changes, write errors, mismatched or failed readback, and Unicode/quotes/pipes transported as JSON. Each bridge invocation can attempt at most one write. Test the default Codex hook and explicit Claude hook, including unknown clients, malformed inputs, and subagent identities.

For live Codex verification, use a dedicated new task after the normal hook trust flow. Check first-response naming, stable titles on follow-up, no parent renaming by subagents, and no batch renaming on resume.

For live Claude Code verification, create a dedicated project and sessions normally. Confirm workspace trust before testing; use a session-scoped hook before merging a global hook. Check explicit Chinese and English naming, first-turn automatic naming, continuation, resume, preservation of a manual custom title, and readback after reopening. Keep session IDs, logs, test files, environment details, and run results in private records outside this repository. A documented implementation or passing mock test is not a claim that a live client was verified.
