# Naming behavior acceptance checks

Read this for maintenance or release, not routine naming. Keep three kinds of evidence separate: deterministic script/package tests, independent offline Agent simulations, and actual client activation. None substitutes for the next.

## Structured current-task evaluation

[cases.json](../evals/cases.json) is the source of truth for the structured inputs and expectations. It covers first-turn Chinese/English/Traditional Chinese naming, quoted language instructions, user-chosen and compliant titles, lifecycle preservation, missing dates, exact names, preview/diagnosis, file-only and broader no-change requests, subagents, unavailable tools, readback failures, concurrent edits, explicit normalization, and Claude startup/custom-title/fork behavior.

From the repository root:

```sh
python3 -m unittest discover -s skills/agent-task-namer/scripts
python3 -m unittest discover -s hooks
python3 skills/agent-task-namer/scripts/eval_cases.py check
```

`check` validates the fixture structure, not Agent decisions. SDK tests use mocks. Package tests relocate the plugin, check its release pin and resources, and run the standalone skill without plugin files. They do not install or trust a plugin.

### Blind simulation

1. Copy the skill to an isolated temporary directory before editing to preserve the baseline. Export from that copy's `scripts/eval_cases.py export`. For the updated run, export from the updated copy. Export injects the matching copy's actual Hook reminder and excludes expectations.
2. Give an independent evaluator only the exported inputs, the matching `SKILL.md`, and the relevant client references. Do not give it this document, the fixture's expected section, tests, earlier evaluator results, or your suspected failure. The exported protocol defines the response format. The evaluator role-plays each case independently using the fictional tool snapshots; it must never call actual task tools or SDKs.
3. Ask the evaluator to write a results JSON array outside the repository. Each result contains `id`, `action`, `title`, `verified`, an ordered `trace` of `read`/`write`/`readback`, and a short `reason`. Include candidate/preview titles in `title`, not only in the reason. A preserved title is the actual original title. These are proposed operations, not captured execution traces.
4. Grade each run against the same expectations:

```sh
python3 skills/agent-task-namer/scripts/eval_cases.py export > /tmp/task-namer-inputs.json
# Have the independent evaluator read the exported inputs and write its results.
python3 skills/agent-task-namer/scripts/eval_cases.py grade /tmp/task-namer-results.json
```

Use a unique private temporary directory when multiple runs are active. Export has no model runner, network calls, live-client access, or new dependencies. `grade` exits nonzero for failed checks, incomplete results, unknown/duplicate IDs, or malformed input.

5. Manually review topic meaning and language, and whether the reasoning uses only supplied evidence. The grader checks action, write count/order, exact protected titles, and required category/date prefixes; it cannot judge all semantic quality. Topic wording may vary. Missing-date and subagent cases allow preserving the original title rather than forcing an optional suggestion. The file-existence case accepts Explore or Research but still requires an English title and the correct date.
6. Investigate failures before editing rules. Distinguish a response-format failure from a naming error, and an overly strict expectation from a real regression. Record any expectation corrections, then grade both versions consistently. Rerun affected cases after a rule change. Do not call a single passing simulation proof of reliability across models or live clients.

Keep prompts containing personal context, run results, model/environment details, and troubleshooting records outside the repository. Publish reusable fictional cases only. Never pass a fictional case ID to real tools.

## Additional manual scenarios

These extend the structured current-task cases without duplicating their expectations. Evaluate with the same blind-input method; supply only the scenario, not the expected result. Task names below are fictional. Unless specified otherwise, identity/tools and authorization are confirmed; creation is `2026-09-04T00:00:00Z` and the main request is Chinese.

### Context and language

- **Closing exchanges:** The newest two turns contain “提交代码” and “push”; an earlier page, available on request, records “修复登录回调失败”. Expect the evaluator to obtain that page and classify the final goal as Fix, not Release.
- **Japanese:** The substantive request is “ログイン時のコールバックエラーを修正してください。” plus English logs. Expect Japanese category/topic, the fixed bug emoji, and Shanghai creation date `260904`.
- **Per-task batch language:** A Chinese request authorizes organizing two tasks. One's goal is “Write a deployment guide for Atlas.” followed by “OK/push”; the other's is “编写 Atlas 部署教程”. Expect English Docs and Chinese 文档 respectively, with `260904`.
- **Explicit translation:** The current title is `🐛 修复 | 260904 | 登录回调失败`. The user asks to translate it into English while keeping the format. Expect a verified English title. Without an explicit translation request, English continuation preserves the Chinese title.
- **Unknown host:** Only a model name containing “Claude” is supplied, without confirmed host/title tools. Expect suggestions only, with no host inference. A generic host with missing creation time gets an explicitly undated draft, not a fabricated date.

### Batch membership, interruption, and restoration

Use [batch.md](batch.md) as the execution protocol, including recording before writes and at most two prepared writes per operation.

| Scenario | Expected behavior |
|---|---|
| Organize project A: current official `projectId=null`, but old assignment/sidebar records say A | Exclude it; official null takes priority. |
| Task absent from official list, no explicit assignment, confirmed sidebar association to A; official read confirms an unarchived main task with no conflict | Include the confirmed task. Directory match alone for a different task leaves membership unknown. Do not claim inventory completeness. |
| Compliant title `🔍 探索 | 260904 | 远程连接配置`, resumed and normalized again in 2027 | No write and no date change. |
| `before=原名`, `after=目标名`, `writing`, `attempts=1`; current title is target | Read and mark verified, without another write. |
| Same record; current title is original | Persist `writing, attempts=2` before a retry, then read back. |
| Same record; current title is a third title | Mark conflict and preserve it. |
| `writing, attempts=2`; current title is original | Read only; never prepare a third write. |
| First restoration requested from `verified, attempts=1`; current title is target | Reset count for the new restoration operation; persist `restoring, attempts=1`, write original, read back before `restored`. |
| Restoration requested; current title is original or a third title | Original: verify without writing. Third title: conflict. |
| Interrupted `restoring, attempts=1`; test target/original/third titles | Read first; retry only target, preserving the count. Original completes; third conflicts. |
| `restoring, attempts=2`; current title remains target | No further write, preserve unverified status. |
| Completed `restored` entry later externally changed back to target | Conflict; do not restore it again using the old record. |
| `pending, attempts=0`; first pre-write read already equals target | Mark skipped; do not count as this batch's write or restore it later. |
| User requests updating the Skill, with no task-set naming authorization | No renaming of other tasks. |
| Claude user asks to restore a Codex batch record | Explain current-session-only scope; do not access or restore the record. |

### Diagnosis and migration

Use [troubleshooting.md](troubleshooting.md), supplying snapshots rather than live configuration.

- A repository checkout and standalone copy exist, but the host catalog and sole Hook point to the standalone copy. Inspect that loaded copy; two directories do not prove duplicate execution or an installed update.
- A synthetic Hook returns JSON and shell Python works, but desktop PATH, trust, dispatch and title readback are unavailable. Report only the script stage as passed. Do not infer trust status, change configuration, or inspect private logs/databases.
- The user authorizes migration from standalone to a trusted enabled plugin. Snapshots show both naming hooks, an unrelated hook and customized Skill files. Remove only the obsolete naming-hook entry within that authorization; preserve unrelated hooks/customizations, and do not register the plugin Hook twice. Verify dispatch separately.

## Live release gate

Use a dedicated new local Codex task after normal installation and Hook trust. Verify first-response naming, follow-up stability, user-chosen title preservation, resume, disabling, and no parent renaming by subagents. Include a new task whose request limits changes to project files: it should still receive the authorized title metadata update. Never use real historical tasks as fixtures.

Record these stages separately: package checks; installed copy and visible trust; actual reminder dispatch; authorized write and matching readback; continuation/disable behavior. A passing existing installation does not verify a newly edited checkout. Do not update publication claims or point the marketplace at an unreleased tag based on offline results alone.

For Claude, use a dedicated project/session, normal workspace trust, and a session-scoped Hook first. Check explicit Chinese/English naming, first-turn naming, custom-title preservation, resume/fork, and readback after reopening. Keep its live results separate and retain the experimental label until verified. A documented bridge and mocked SDK tests do not establish live Claude support.
