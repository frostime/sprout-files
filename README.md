# sprout CLI (v0.1)

`sprout` 是一个项目内模板驱动的文件/目录生成 CLI，面向 Agent 协同开发场景。

## 核心特性

- 从当前目录向上查找首个 `.sprout/`（类似 `.git`）
- 命令包目录：`.sprout/commands/<command>/`
- 输入模式：支持 `key=value`、`--json`、`--json-file`
- TTY 下缺参可引导进入交互模式，非 TTY 下快速失败
- 冲突策略：`fail` / `overwrite` / `skip` / `rename`
- 支持生成后执行 `post` actions
- 运行时兼容 `yaml` / `yml` / `json` 配置与 manifest
- 内置文档通过 `sprout doc` 访问

## 快速开始

```bash
# 0) 安装（开发中使用 uv）
uv sync

# 1) 初始化
uv run sprout init --with-examples

# 2) 查看命令
uv run sprout list --all

# 3) 执行命令
uv run sprout new issue name=my-task type=bug

# 4) 结构化输入
uv run sprout new issue --json '{"name":"my task","type":"bug"}'
uv run sprout new issue --json-file ./inputs.json

# 5) 预览
uv run sprout new issue name=test type=feat --dry-run
```

## CLI 命令

```bash
sprout init [--profile minimal|docs] [--profile-file ./profile.json] [--with-examples]
sprout list [--all]
sprout doctor
sprout doc list
sprout doc show <name>
sprout doc path <name>
sprout new <command> [key=value ...] [--json '{...}' | --json-file ./inputs.json] [--set key=value] [-i|--interactive] [--no-input] [-n|--dry-run] [--conflict fail|overwrite|skip|rename]
```

## `.sprout/` 结构

```text
.sprout/
  config.yaml
  commands/
    issue/
      manifest.yaml
      issue.md
```

## 文档入口

- `README.md`：项目概览与快速开始
- `sprout doc show user-guide`：CLI 使用手册
- `sprout doc show command-authoring-guide`：命令包编写手册（面向维护者 / Agent）

边界约定：
- `user-guide` 讲“怎么使用 sprout”
- `command-authoring-guide` 讲“怎么编写 `.sprout/commands/*`”

## Agent 协作建议

如果让 Agent 帮你编写 `.sprout` 命令包，先让它读取：

```bash
sprout doc show command-authoring-guide
```

然后先对齐：
1. 命令目的
2. 输入字段及类型
3. 输出文件/目录
4. 冲突策略

## 常用检查

```bash
sprout list --all
sprout doctor
sprout new <command> name=test
sprout new <command> --json '{"name":"test"}'
sprout new <command> name=test --dry-run
```

## 常见问题

- **找不到项目模板根**：确认当前目录或父目录存在 `.sprout/`
- **命令不可用**：执行 `sprout doctor` 检查 invalid/conflict 报告
- **YAML 无法读取**：安装 `PyYAML`，或改用 JSON
- **想查看内置文档路径**：执行 `sprout doc path user-guide` 或 `sprout doc path command-authoring-guide`
