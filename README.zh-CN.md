# Agent Task Namer

[English](README.md)

为 Codex 任务自动添加类型、创建日期和主题，让侧栏里的任务更容易找到。

![任务标题命名前后对比：统一显示类型、创建日期和主题](assets/readme/before-after-zh.png)

*命名效果示意：同一组任务，统一类型、创建日期与主题。*

```text
🐛 修复 | 260904 | 登录回调失败
📝 文档 | 260904 | Atlas 部署教程
🐛 Fix | 260904 | Login callback failure
```

标题跟随各任务主要提问的语言。日期使用任务创建当天，默认按北京时间计算，续聊不变。你明确指定的标题会保留。

## 在 Codex 中开始使用

适用于具备官方任务读取、改名工具的 **Codex 桌面端本地任务**。自动命名还需要 **Python 3**，并完成下方的一次性配置。

目前推荐安装独立 Skill。把这句话发给 Codex：

```text
请从 https://github.com/deronendless/agent-task-namer/tree/main/skills/agent-task-namer 安装 agent-task-namer 这个 Skill。
```

安装后，先试着给当前任务命名：

```text
$agent-task-namer 按规范重命名当前任务。
```

侧栏标题应变成上方示例中的格式。已经准确合规的标题会保留；缺少可靠创建时间时只生成类型和主题草稿，不猜日期。

## 让新任务自动命名

装好独立 Skill 后，发送：

```text
$agent-task-namer 帮我启用新任务自动命名。
```

按客户端提示完成首次 Hook 信任，然后新建一个本地任务，像平常一样提问，例如“帮我修复登录报错”。首次实质请求明确后才会命名，打开空任务不会命名。续聊、恢复旧任务不会触发新的自动改名。

**插件安装方式：**本仓库也已将 Skill 和启动 Hook 打包成 Codex 插件。已在作者本机验证本地安装与自动命名，尚未公开上架。如果你已经安装插件，在详情页审阅 Hook 并点击 **Trust all** 即可，无需单独配置 Hook。从独立 Skill 切换时，请查看[配置与迁移说明](skills/agent-task-namer/references/automatic.md)。

没有生效时，直接发送：

```text
$agent-task-namer 检查一下为什么没有自动命名。
```

[故障排查](skills/agent-task-namer/references/troubleshooting.md)列出了检查项和对应处理方式。

## 更多用法

- **预览或整理 Codex 任务：**让 `$agent-task-namer` “预览新标题，先不要执行改名”，或“整理当前项目的所有任务命名”。[批量改名与恢复](skills/agent-task-namer/references/batch.md)。
- **切换语言：**直接说“保留格式，把当前任务标题改成英文”。
- **Claude Code 本地 CLI（实验性）：**将 `skills/agent-task-namer/` 复制到 `~/.claude/skills/agent-task-namer/`，[安装可选 SDK](skills/agent-task-namer/references/automatic.md#claude-code-local-cli-setup) 后使用 `/agent-task-namer 按规范重命名当前会话。` 完整流程仍待验证，暂不支持批量整理与恢复。
- **其他 Agent：**加载 [Skill](skills/agent-task-namer/SKILL.md) 后生成标题建议，不提供直接改名。

---

[完整规则](skills/agent-task-namer/SKILL.md) · [MIT 许可证](LICENSE)

完整规则与参考文档使用英文。社区 Skill，非 OpenAI 或 Anthropic 官方产品。
