## Why

Agent 协同开发场景下会频繁创建结构化文档（如 issue/change）。当前每个项目都要维护专用脚本，导致规则分散、重复实现、迁移成本高。需要一个统一 CLI，把“模板定义 + 输入收集 + 资产生成”抽象为可复用能力。

## What Changes

- 新增统一 CLI（命名为 `sprout`），用于在项目内按命令生成文件/目录资产。
- 引入项目本地配置根目录 `.<cli-name>/`（当前为 `.sprout/`），并以命令包形式组织定义（避免占用 `templates/`）。
- 支持 `sprout new <command>` 生成流程：参数输入（默认）+ `-i/--interactive` 交互输入（可选）。
- 支持基础输入类型（`string`/`number`/`enum`），其中 `number` 支持可选 `min/max` 约束；模板语法使用纯文本变量插值（`{{name}}`）。
- 增加发现与冲突规则：从当前目录向上查找首个配置根并停止；同一项目内命令同名冲突时双方禁用并告警。
- 目标路径冲突策略改为可配置：`fail` / `overwrite` / `skip` / `rename`。
- 增加 `sprout init` 基础初始化能力，支持自定义骨架，并在项目内落地 `sprout-authoring` Skill 文档（不依赖全局安装），可选附带示范命令包。

## Capabilities

### New Capabilities
- `project-command-discovery`: 在项目内发现并加载命令包，支持向上查找首个配置根并进行有效性校验。
- `template-asset-generation`: 基于命令定义收集输入、执行变量插值并生成文件/目录资产。
- `agent-assisted-template-authoring`: 提供 init + 本地 Skill 文档，支持 Agent 辅助搭建和维护模板命令结构。

### Modified Capabilities
- None.

## Impact

- 新增统一 CLI 的命令发现、配置解析、插值渲染与落盘流程。
- 新增项目级模板规范与校验规则，替代项目特化脚本分叉。
- 影响 Agent 协同流程：通过 `sprout init` + `sprout-authoring` 提升模板维护效率与一致性。
