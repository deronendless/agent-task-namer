# Diagnose automatic naming

Use this for an explicit report that automatic naming did not run. Diagnosis takes precedence over a startup naming reminder; do not rename the diagnostic task to demonstrate a fix. A request to inspect is read-only. When the user also requests installation, migration, repair, or a particular rename, use that existing authorization for the relevant action and follow [automatic.md](automatic.md) or the [naming workflow](../SKILL.md#current-task-workflow). Do not ask for the same authorization again.

## Locate the failure and separate unknowns

Collect only the evidence needed for the reported failure. Locate the earliest confirmed failure and keep unavailable checks separate; one unknown must not stop other relevant, independent read-only checks. Do not read session databases, private transcripts, private logs, or trust records. Read configuration narrowly: extract only this skill's source, hook event, command, matcher, and enabled state, without dumping whole configuration files, environment variables, credentials, or unrelated hooks. Use current official client documentation if the installed client's configuration behavior is unclear.

1. **Client capability.** Identify the actual host from trusted runtime context. In Codex, check whether the current environment exposes official task reading and title writing; the presence of a Codex executable or an installed skill is insufficient. Read only the current task if its identity is confirmed and metadata is needed. In Claude Code, check the current-session identity, optional SDK bridge, and supported metadata as described in [clients.md](clients.md). Claude Code support remains experimental. Missing capabilities explain candidate-only behavior; do not call a write operation as a capability test.
2. **Loaded copy.** Record the actual `SKILL.md` path supplied by the host's skill catalog or trusted hook, and check that copy's scripts and references. Resolve symlinks when comparing it with a checkout or another installed copy. A Git checkout update does not update an independent installed copy. If multiple candidates exist but the host does not reveal which was loaded, mark the loaded copy as unverified instead of choosing the newest one. Finding files alone does not prove discovery or activation.
   For repository-marketplace installations, `codex plugin marketplace list` identifies the configured source and resolved snapshot, while `codex plugin list --marketplace agent-task-namer` checks catalog visibility. Neither command alone proves that the plugin is installed, enabled, or current.
3. **Interpreter and package.** Inspect the matching hook's command before running anything. Resolve its interpreter and script path, including the plugin-provided `PLUGIN_ROOT` where applicable, and check the interpreter version and file accessibility. Codex's hook needs Python 3; only Claude's optional bridge needs its separate Python/SDK environment. A shell's `python3` being available does not establish that the desktop hook has the same `PATH`. If the actual hook environment is unavailable, keep that part unverified. A synthetic `SessionStart` input to the inspected bundled script may confirm JSON output, but neither runs a real client event nor proves a title changed.
4. **Registration and trust.** Inspect the relevant installed plugin manifest/bundled hook or standalone hook configuration; see [automatic.md](automatic.md) for client-specific locations. Check the event, matcher, enabled state, and the command's target. A standalone Skill does not itself register a lifecycle hook. Check trust through the client's supported Hooks or plugin UI when available, or distinguish the user's reported trust from directly observed status. If no supported surface exposes it, report trust as unverified; do not infer “untrusted” from a missing title. Never edit trust records or bypass the client's trust flow.
5. **Duplicate sources.** Compare the enabled plugin hook with matching standalone hook entries. Two installed Skill directories alone are not evidence of duplicate hook execution. Report duplicate registration only when both sources would run this naming reminder for the same event; execution remains unverified until observed. For an authorized migration, retain the chosen installation, remove only the obsolete naming-hook entry, and verify that unrelated settings retain their previous values. Preserve a customized old Skill without deleting, overwriting, or automatically merging it into the plugin cache. Do not register an enabled plugin's bundled hook again in user configuration.
6. **Naming eligibility.** If the reminder reached the main agent, check whether this was actually a new task's first substantive turn, whether the creation timestamp and current title were readable, and whether the title was already correct or user-chosen. Resume, clear, compact, fork, preview, diagnosis, and missing evidence can correctly leave a title unchanged. Do not “repair” those cases by weakening the language, creation-date, identity, or user-title rules.

When a cause is established, explain it and give the smallest next action. If the available evidence cannot distinguish causes, name the specific missing check instead of claiming a fix. An unsupported UI or unavailable hook environment is a limit of this check, not evidence that the user's installation is broken.

## Short result

Reply in the user's language. Omit empty fields and avoid printing machine details unless they help the user locate the problem:

```text
结论：<已确认原因，或目前尚不能定位>
已确认：<直接观察到的能力、加载副本或配置事实>
未验证：<例如桌面 Hook 的 PATH、客户端信任状态、真实新任务触发>
下一步：<一个具体操作；已授权修复时说明实际完成的修改>
验证结果：<脚本通过 / 提醒已触发 / 标题已读回；只列实际完成的阶段>
```

“Hook output passed,” “configuration saved,” and “plugin installed” do not establish that automatic naming is fixed. A title is verified only after a supported client read returns the intended value following an authorized naming action.

## Verify in stages

Keep the stages distinct in reports; do not turn a diagnosis into creating tasks or changing titles without a request for that action. Use the [acceptance checks](validation.md) for maintenance or an authorized live test:

| Stage | What the evidence establishes |
|---|---|
| Package and offline script tests | Required files resolve and the script emits valid reminders; no live installation is established. |
| Installation, registration, and visible trust | The intended copy and hook are configured; actual dispatch remains unverified. |
| A dedicated new task receives the reminder | The client dispatched this hook; title reading, naming decisions, and writing are separate. |
| First substantive request, supported write, and matching read-back | Automatic naming worked for that tested task and environment. |
| Follow-up, user-title preservation, resume, and disabling | Each checked behavior works; report untested cases separately. |

Keep private test records outside the repository. A passing Codex check does not establish Claude Code support, and passing mock SDK tests do not remove its experimental status.
