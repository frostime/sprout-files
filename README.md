# sprout CLI (v0.1)

`sprout` 是一个项目内模板驱动的文件/目录生成 CLI，面向 Agent 协同开发场景。

## 核心特性

- 发现规则：从当前目录向上查找首个 `.sprout/`（类似 `.git`）
- 命令包目录：`.sprout/commands/<command>/`
- 输入模式：默认参数输入；`-i/--interactive` 才进入交互
- 基础类型：`string` / `number` / `enum`（`number` 支持可选 `min/max`）
- 插值语法：`{{name}}`（仅纯文本替换，不支持逻辑流）
- 冲突策略：`fail` / `overwrite` / `skip` / `rename`
- `init` 支持自定义骨架、可选示例命令包，并生成项目内 `sprout-authoring` Skill 文档

## 快速开始

```bash
# 1) 初始化
sprout init --with-examples

# 2) 查看命令
sprout list --all

# 3) 执行命令（默认参数模式）
sprout new issue name=my-task type=bug

# 4) 缺参时使用交互模式
sprout new change -i
```

## 命令

```bash
sprout init [--profile minimal|docs] [--profile-file ./profile.json] [--with-examples]
sprout list [--all]
sprout doctor
sprout new <command> [key=value ...] [--set key=value] [-i|--interactive] [--conflict fail|overwrite|skip|rename]
```

## `.sprout/` 结构

```text
.sprout/
  config.json
  commands/
    issue/
      manifest.json
      issue.md
  skills/
    sprout-authoring/
      SKILL.md
```

## 命令包 `manifest.json`（示例）

```json
{
  "name": "issue",
  "description": "Create issue",
  "inputs": [
    { "name": "name", "type": "string" },
    { "name": "type", "type": "enum", "enum": ["bug", "feat", "refactor"] },
    { "name": "priority", "type": "number", "min": 1, "max": 5, "default": 3 }
  ],
  "assets": [
    { "type": "dir", "path": "issues" },
    { "type": "file", "path": "issues/{{YY}}-{{MM}}-{{DD}}_{{name}}.md", "template": "issue.md" }
  ]
}
```

## 变量上下文

除了输入变量，内置时间变量：

- `YYYY`, `YY`, `MM`, `DD`
- `hh`, `mm`, `ss`
- `date`, `time`, `datetime`, `timestamp`

## 常见问题

- **找不到项目模板根**：确认当前目录或父目录存在 `.sprout/`
- **命令不可用**：执行 `sprout doctor` 检查 invalid/conflict 报告
- **YAML 清单无法读取**：安装 `PyYAML` 或改用 `manifest.json/toml`
