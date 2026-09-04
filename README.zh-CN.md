# Agent Task Namer

[English](README.md)

给 Agent 任务统一命名，让任务更好找。支持 Codex、Claude Code 本地 CLI，以及其他 Agent 的标题建议。

```text
🐛 修复 | 260904 | 登录回调失败
📝 文档 | 260904 | Atlas 部署教程
🐛 Fix | 260904 | Login callback failure
```

标题跟随各任务主要提问的语言。日期使用任务创建当天，默认按北京时间计算，续聊不变。

| 客户端 | 当前任务改名 | 可选自动命名 | 批量整理与恢复 |
|---|---|---|---|
| Codex（需要官方任务工具） | 支持 | 支持 | 支持 |
| Claude Code 本地 CLI（需要可选 SDK） | 本地标题读写已实测 | 完整流程待验证 | 暂不支持 |
| 其他能读取 Skill 的 Agent | 仅标题建议 | 暂不支持 | 暂不支持 |

实测环境与验证状态见[验证记录](references/validation.md)。

## 1. 安装

把这句话发给你使用的 Agent：

```text
请从 https://github.com/deronendless/codex-task-namer 安装 codex-task-namer 这个 Skill。
```

Claude Code 安装到 `~/.claude/skills/codex-task-namer/`，实际改名还需[安装可选 SDK](references/automatic.md#claude-code-local-cli-setup)。其他 Agent 按其 Skill 安装方式加载，或直接读取本仓库的 `SKILL.md`。仓库名和 Skill 标识继续使用 `codex-task-namer`。

## 2. 使用

**Codex：给当前任务改名**

```text
$codex-task-namer 按规范重命名当前任务。
```

**Claude Code：给当前会话改名**

```text
/codex-task-namer 按规范重命名当前会话。
```

**其他 Agent：生成建议**

```text
读取 codex-task-namer/SKILL.md，按本任务的主要请求生成标题建议。
```

缺少可靠创建时间时只生成类型和主题草稿，不猜日期。

**Codex：先看项目预览**

```text
$codex-task-namer 预览当前项目各任务的新标题，先不要执行改名。
```

**Codex：整理整个项目**

```text
$codex-task-namer 整理当前项目的所有任务命名。
```

已经准确合规、或由你明确指定的标题会保留。想切换语言，直接说：“保留格式，把当前任务标题改成英文。”

## 可选：新任务自动命名

把这句话发给 Codex 或 Claude Code：

```text
帮我启用 codex-task-namer 的新任务自动命名。
```

自动命名需要单独配置和客户端支持，不会随安装自动启用。按对应客户端的提示审阅配置并完成信任流程。[查看配置详情](references/automatic.md)。

---

[完整规则](SKILL.md) · [批量改名与恢复](references/batch.md) · [验证方法](references/validation.md) · [MIT 许可证](LICENSE)

完整规则与参考文档使用英文。社区 Skill，非 OpenAI 或 Anthropic 官方产品。
