# Codex Task Namer

[English](README.md)

给 Codex 任务统一命名，让侧边栏里的任务更好找。

```text
🐛 修复 | 260904 | 登录回调失败
📝 文档 | 260904 | Atlas 部署教程
🐛 Fix | 260904 | Login callback failure
```

标题跟随各任务主要提问的语言。日期使用任务创建当天，默认按北京时间计算，续聊不变。

## 1. 安装

把这句话发给 Codex：

```text
请从 https://github.com/deronendless/codex-task-namer 安装 codex-task-namer 这个 Skill。
```

安装完成后，从下一轮开始使用。需要 Codex 客户端支持读取和修改任务标题。

## 2. 使用

**给当前任务改名：**

```text
$codex-task-namer 按规范重命名当前任务。
```

**先看效果，不立即改名：**

```text
$codex-task-namer 预览当前项目各任务的新标题，先不要执行改名。
```

**整理整个项目：**

```text
$codex-task-namer 整理当前项目的所有任务命名。
```

已经准确合规、或由你明确指定的标题会保留。想切换语言，直接说：“保留格式，把当前任务标题改成英文。”

## 可选：新任务自动命名

把这句话发给 Codex：

```text
帮我启用 codex-task-namer 的新任务自动命名。
```

自动命名需要单独配置和客户端支持，不会随安装自动启用。按 Codex 提示审阅并信任配置。[查看配置详情](references/automatic.md)。

---

[完整规则](SKILL.md) · [批量改名与恢复](references/batch.md) · [验证方法](references/validation.md) · [MIT 许可证](LICENSE)

社区 Skill，非 OpenAI 官方产品。
