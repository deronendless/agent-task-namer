# Batch naming for project tasks

This workflow and its execution-record format are for Codex only; Claude Code and other agents must not use it for batch writes or restoration.

Use only when the user explicitly authorizes naming tasks in a project or a specified set. Once authorization is clear, proceed after the checks below; requests for a plan or preview still produce suggestions only.

## Build a complete inventory of the requested scope

- Determine scope from project membership in the app or the task set specified by the user. Distinguish main tasks, subagents, archived tasks, and other projects. Exclude subagents, archived tasks, and other projects by default; archived main tasks may be included when the user explicitly requests them.
- Check the list using the official `list_threads` and project tools first. Results may be capped: in one local run, a project with 89 tasks returned only the 50 most recent tasks, even with a larger `limit`. This observation is a reason to check completeness, not a permanent count or API guarantee.
- Apply this priority to membership evidence: an explicit `projectId` from the current official tools takes precedence, including an explicit `null` (no project membership). A missing field or a task absent from the list is not equivalent to `null`. Older local records must not override current official membership.
- For tasks absent from the official list, you may inspect local project and task metadata read-only within existing access permissions. Check both explicit assignments and sidebar project-task associations; do not treat the explicit assignment table as a complete inventory. Fields may vary between versions, so inspect the actual structure rather than relying on a fixed database version or path. Skip conflicting metadata when current membership cannot be established. A matching working directory is only a clue, not proof of membership.
- Deduplicate by ID and reconcile the scope counts. If the tools cannot paginate and the inventory cannot be completed reliably, process only the confirmed set and state that the remaining scope is unknown. Do not describe a recent-task list as "all tasks." Do not read other projects merely to reach an expected count.

## Read tasks and propose titles

Call the official `read_thread` in small parallel batches, starting each task with `turnLimit: 2, includeOutputs: false`. Two turns are only the initial window. If they contain only confirmations, commit requests, or other closing exchanges, read the necessary earlier context using the main skill's rules for identifying the substantive task. Extract only the actual title, `createdAt`, and the user goal or actual deliverable supporting the topic; do not output the full tool history.

Use recent goals to identify the actual topic. An initial request to "learn about a project" may have developed into "write a deployment guide" or "remove duplicate skills"; do not mechanically preserve the initial title. Read another page if the content is insufficient. Keep the current title when only unavailable images remain and no useful text is available. A clear user request is enough to establish the topic; a final response is not required.

Apply the main skill's rules for language, dates, categories, exact-title precedence, and idempotence. Determine each task's title language from its substantive user request; do not use the language of the current batch-management request unless the user explicitly requests one language for the batch. Routine batch normalization must not overwrite known user-chosen titles. Skip entries whose project membership cannot be confirmed. Missing creation time, substantive topic, or language is a reason to skip only when naming by the template; entries with an exact new title explicitly specified by the user do not need those inferences. Continue with other confirmed entries.

## Local execution record

Before batch writes, save a JSON array as the execution record and update it after each entry. Store it in a separate local directory, such as `$CODEX_HOME/task-naming-runs/`, or `~/.codex/task-naming-runs/` when `CODEX_HOME` is unset, and provide the path in the final response. Write a temporary file first, then replace the record atomically so an interruption cannot leave a partial record. If saving or updating the record fails, stop further writes and preserve the last valid file and the candidates.

Each array entry contains only the fields below. Preserve the original `createdAt` value. If no candidate can be determined, set `after` to `null` and `status` to `skipped`:

```json
{
  "id": "task ID",
  "before": "original title read from the task",
  "createdAt": 1788403983,
  "after": "🐛 修复 | 260903 | 登录回调失败",
  "status": "pending",
  "attempts": 0,
  "reason": "brief naming rationale or reason for skipping"
}
```

`before` and `after` always mean the original title and the candidate title; do not swap them during restoration. `attempts` counts writes prepared for the current operation and starts at 0. Increment it and persist it with the status before every write-tool call, with at most 2 attempts: the initial attempt and one targeted retry. Reset it to 0 only when first switching from naming to restoration; do not reset it after an interrupted restoration. If an older record lacks a status or attempt count, recover that information from trusted execution records first. If it cannot be confirmed, perform read-only checks; never treat an unknown count as 0.

The statuses mean:

| status | Meaning |
|---|---|
| `pending` | Candidate saved; no write attempted yet |
| `writing` | A write has been prepared or may have occurred; read-back confirmation is pending |
| `verified` | A write in this batch has been read back, and the current title equals `after` |
| `restoring` | Restoration has been prepared or may have occurred; read-back confirmation is pending |
| `restored` | A read-back confirms that the current title equals `before` |
| `skipped` | No write made: already compliant, no action needed, or insufficient evidence |
| `failed` | It is certain that no write occurred and this run cannot continue; record the reason in `reason` |
| `conflict` | An external rename or membership conflict was detected; preserve the current state |

Keep only the necessary titles, times, statuses, attempt counts, and short reasons. Do not copy conversations, screenshots, or full tool output. This is the user's local execution record; do not add it to the skill or a Git repository.

## Write and read back

1. Before execution, use the official tools to read the current title again and check current membership. Proceed only if the title equals `before`. If an entry with no prior write attempt already equals `after`, mark it `skipped`; do not claim it as a successful write by this batch or restore it later. Mark any other title or a membership conflict as `conflict`. If the content has materially changed, determine the candidate again first.
2. **Set the status to `writing`, increment `attempts`, and persist the record before calling the rename tool.** Use only the official `set_thread_title` with the verified `threadId`; omit that argument for the current task. Read-only metadata inspection to complete the inventory does not authorize database changes. Do not use SQL, file edits, or simulated internal APIs to bypass tool restrictions.
3. Read back with the official `read_thread`; mark `verified` only if the current title equals `after`. If the tool response is ambiguous, read-back fails, or the title still equals `before`, keep `writing` and explain why. A successful tool response is not successful verification. If the current title becomes a third title, mark `conflict` and stop overwriting it. Independent reads may run in parallel; dependent checks, record persistence, and writes must run in order.
4. When resuming after interruption or retrying, read again first; never skip verification based only on the log status. For a `writing` entry, a current title equal to `after` means mark `verified`. Continue only if it equals `before`, remains within the authorized scope, and `attempts < 2`; mark any other title as `conflict`. If the attempt limit has been reached or the outcome is still unclear, retain the unverified status. Do not reset the count when resuming. Do not automatically rewrite a `verified` entry whose current title has changed. A generic "continue" must not rename a restored batch again.
5. Report counts from the records after read-back, separating verified entries, entries skipped without a write, conflicts or failures, entries still awaiting verification, and inventory completeness. Describe the requested scope as complete only if the inventory is complete and no unresolved entries remain. Pending verification does not count as success.

## Restore original titles

Run only after the user explicitly requests restoration of this batch or specified entries. Process only entries where this batch previously attempted a write: `writing`, `verified`, `restoring`, or `restored`. Do not automatically include previews, `pending`, `skipped`, `failed`, or entries already marked as conflicting.

- For an entry already marked `restored`, verify only: if the current title still equals `before`, keep it complete. Mark any other title, including a title changed back to `after`, as `conflict`. Do not write again based on the old batch, which could overwrite an external rename made after restoration completed.
- Check task identity, the user's requested restoration scope, and the current title first. If restoration is limited to a project, check current membership. If the title already equals `before`, mark `restored` without writing. Restore only if it equals `after`; if it equals neither, mark `conflict` and preserve the external rename.
- **Set the status to `restoring`, increment `attempts` for the restoration operation, and persist the record before using the official tool to write `before`.** Mark `restored` only when read-back confirms `before`. Otherwise, keep `restoring`; do not swap `before` and `after` or clear the original record.
- After an interrupted restoration, follow the same read-before-action process: a title equal to `before` is complete. Retry only if it equals `after`, authorization still applies, and `attempts < 2`; stop overwriting any other title. Once the restoration attempt limit is reached, perform read-only checks and make no further writes.

Repeated runs process only tasks that still need changes. Do not add deduplication numbers, update titles to the current date, or polish topics that are already accurate.

When the available tools lack conditional writes, a pre-write check is not an atomic lock. Skip a task if external changes to it are ongoing; do not promise to eliminate all concurrent overwrites.
