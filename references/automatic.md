# 自动触发的安装与维护

仅在用户要求安装、启用、调整或移除自动命名时读取。日常改名不需要配置 Hook。

## 运行方式

单独安装 Skill 只提供显式调用和按描述匹配。`scripts/session_start.py` 为
Codex 的 `SessionStart` 输出 `hookSpecificOutput.additionalContext`，提醒主代理
读取本 Skill。它不调用模型、不读取聊天全文、不执行改名、不保存状态。
`startup`、`resume`、`clear`、`compact` 都只是会话事件，不能据此推定新任务或创建日期。
Skill 决定是否需要命名，并通过当前环境的官方工具执行。

## 本机配置

Hook 可放在 `$CODEX_HOME/hooks.json`（通常为 `~/.codex/hooks.json`），或者对应的
`config.toml` 中。添加前检查现有定义，保留其他 Hook，避免重复注册本脚本。
多个来源的 Hook 会合并执行，不应以覆盖整个文件的方式安装。

以下是配置形状；安装时将路径替换为本机实际绝对路径，使用已验证的 Python 3
解释器，并正确引用路径中的空格：

```json
{
  "hooks": {
    "SessionStart": [{
      "matcher": "^(startup|resume|clear|compact)$",
      "hooks": [{
        "type": "command",
        "command": "python3 /absolute/path/codex-task-namer/scripts/session_start.py",
        "timeout": 3,
        "additionalContextLimit": 600
      }]
    }]
  }
}
```

非托管 Hook 必须由用户在 Codex CLI 的 `/hooks` 中审阅并信任。新的或更改后的
Hook 定义在受信任前不会运行。不要编辑信任记录、使用绕过信任参数，或声称保存
配置等于启用成功。若当前环境禁用了 Hook，先说明现状，遵循用户是否启用的选择。

## 验证与迁移

1. 运行 `python3 scripts/test_session_start.py` 验证事件输入、JSON 输出与非阻塞行为。
2. 用户信任 Hook 后，在支持任务工具的 Codex 客户端验证新任务首次回复会命名，
   普通续聊不重复改名，子代理不改父任务，恢复旧任务不批量改名。
3. 只有实际触发验证成功且用户已要求迁移时，才移除全局 `AGENTS.md` 中重复的
   命名段落；保留其他个性化指令。自动触发仍依赖宿主、Hook 信任和可用改名工具。

停用自动命名时，在 `/hooks` 禁用本 Hook，或只移除匹配本脚本的配置项。
Skill 仍可按需使用。不需要定时任务、后台服务或直接修改 Codex 数据库。

官方参考：[Skills](https://learn.chatgpt.com/docs/build-skills)、
[Hooks](https://learn.chatgpt.com/docs/hooks)。
