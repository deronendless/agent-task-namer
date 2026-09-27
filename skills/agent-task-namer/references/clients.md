# Client capabilities and Codex operations

Read only the actual host's workflow: Codex below, [local Claude Desktop Code](claude-desktop.md), or [Claude Code CLI](claude-cli.md) (experimental). Identify the host from trusted runtime context. Loading the Skill does not supply missing tools; other hosts or missing capabilities use the [candidate-only fallback](../SKILL.md#candidate-only-fallback), never a different client's operations.

## Codex

- Confirm the current task ID from trusted runtime context, `CODEX_THREAD_ID`, or the trusted Hook's `session_id`. Do not use an ID copied from older messages or choose another task when identity is uncertain.
- Read the current title, `createdAt`, and needed context through official `read_thread`; start with `turnLimit: 2, includeOutputs: false`. `createdAt` is Unix time in **seconds**. Apply the main Skill's timezone rule. Read earlier history only if the substantive goal/language is unclear; never enumerate tasks just to find this task's date.
- Write with official `set_thread_title`, **omitting `threadId`** for the current task. Then `read_thread` with the confirmed current ID and verify the exact candidate. An ambiguous write requires readback before any targeted retry; follow the main Skill's concurrency and retry limits.
- Explicitly requested batches/restoration use [batch.md](batch.md), including its membership, recording and attempt rules. Local metadata supplements inventory only under that workflow's read-only rules. Never write directly to the Codex database.

## Claude Desktop Code: local sessions

Use [claude-desktop.md](claude-desktop.md): native current-session `self`, Desktop identity and ISO creation time. No SDK bridge fallback.

## Claude Code CLI

Use [claude-cli.md](claude-cli.md): trusted runtime UUID, optional SDK bridge, and epoch-millisecond creation time. Current session only.

### Inspect and read context

The CLI SDK's fields and title-origin guard are documented in [the CLI inspection workflow](claude-cli.md#inspect-and-read-context).
