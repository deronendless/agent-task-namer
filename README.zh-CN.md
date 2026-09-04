# Codex Task Namer

[English](README.md)

自动识别用户提问语言，将 Codex 任务标题整理为统一格式：

```text
emoji 类型 | YYMMDD | 主题

🐛 修复 | 260904 | 登录回调失败
📝 文档 | 260904 | Atlas 部署教程
🐛 Fix | 260904 | Login callback failure
```

## 功能

- 命名当前任务、预览候选标题，或批量整理用户明确指定的项目任务。
- 类型和主题跟随每个任务的实质提问语言，支持简繁中文、英文及其他语言；代码、日志、引用和简短回复不影响判断。
- 日期使用真实创建时间，跨天、跨年续聊保持不变。默认时区为 **Asia/Shanghai**，不会随标题语言改变；用户可明确指定其他时区。
- 保留用户指定的确切标题和已经准确合规的标题。续聊切换语言不会自动翻译已有标题，明确要求翻译时才调整。
- 批量改名保存本地记录，支持中断续作及按记录恢复，并检查期间发生的外部改名。

固定八种类型：✨ 功能、🎨 设计、🐛 修复、⚡ 优化、🚀 发布、🔍 探索、📝 文档、🔬 研究。不同语言使用同一组 emoji 和类别含义。

## 使用条件

需要支持 Skill，并提供官方任务读取与改名工具的 Codex 环境，例如 `read_thread` 和 `set_thread_title`。

**本 Skill 不提供这些工具。** 无法确认任务身份、取得所需工具或可靠创建时间时，会保留标题；用户明确指定确切标题时不需要推断创建时间。不会直接修改 Codex 数据库。

只有可选 Hook 和测试需要 Python 3。脚本仅使用标准库，无需 API Key，也无需安装 Python 第三方依赖。

## 安装

克隆到个人 Skill 目录：

```sh
task_skill_dir="${CODEX_HOME:-$HOME/.codex}/skills/codex-task-namer"
mkdir -p "$(dirname "$task_skill_dir")"
git clone https://github.com/deronendless/codex-task-namer.git "$task_skill_dir"
```

如果目标目录已存在，先检查已有安装，不要直接覆盖。在能发现该目录的客户端中，Skill 将于下一轮可用。

## 使用

向 Codex 提问，例如：

```text
$codex-task-namer 按规范重命名当前任务。
$codex-task-namer 预览当前项目各任务的新标题。
$codex-task-namer 整理当前项目的所有任务命名。
$codex-task-namer 保留格式，把当前任务标题改成英文。
$codex-task-namer 根据我提供的批次记录恢复原来的标题。
```

批量整理会逐个识别任务语言；明确要求统一语言时才统一。批量改名需要用户明确提出，新任务 Hook 提醒不授权修改其他任务。

## 可选：自动命名

安装 Skill 提供显式调用和按描述匹配，**不保证每次新聊天都会自动命名**。

附带的 `SessionStart` Hook 只提醒主代理读取 Skill，不调用模型、不读取聊天全文，也不执行改名。自动命名取决于宿主支持、Hook 信任以及可用的任务工具。`startup`、`resume`、`clear`、`compact` 是会话事件，不是创建时间。

可以让 Codex 按[自动触发安装指南](references/automatic.md)合并现有配置，填写实际解释器和脚本路径，并通过宿主支持的流程审阅和信任 Hook。安装仓库本身不会修改 Hook 配置或信任记录。

## 验证与维护

在仓库根目录运行 Hook 协议测试：

```sh
python3 scripts/test_session_start.py
```

测试不会操作真实任务，也不能代替模型命名决策验收。[行为验收案例](references/validation.md)覆盖日期、多语言、标题保留、批量范围、中断和恢复。

- [SKILL.md](SKILL.md)：命名规则与当前任务流程。
- [批量流程](references/batch.md)：范围确认、本地记录、续作与恢复。
- [Hook 配置](references/automatic.md)：可选安装与触发验证。

核心指令和详细参考文档目前使用中文，输出标题会跟随用户提问语言。批次记录保存在 Skill 目录之外，不应提交到仓库。写前重新读取可以减少误覆盖，但不构成防止并发改名的原子锁。

## 许可证

[MIT](LICENSE)。本项目是社区 Skill，并非 OpenAI 官方产品。
