---
name: improve-cli-interaction
status: DONE
change-type: single
created: 2026-04-11T20:56:38
reference:
  - source: ".sspec/changes/archive/26-04-11T17-33_improve-usability"
    type: "prev-change"
    note: "Follow-up CLI UX polish after usability improvements."
---

<!-- @RULE: Frontmatter
status: PLANNING | DOING | REVIEW | DONE | BLOCKED
change-type: single | sub
reference?: Array<{source, type: 'request'|'root-change'|'sub-change'|'prev-change'|'doc', note?}>

Sub-change MUST link root:
reference:
  - source: ".sspec/changes/<root-change-dir>"
    type: "root-change"
    note: "Phase <n>: <phase-name>"

Single-change common reference:
reference:
  - source: ".sspec/requests/<request-file>.md"
    type: "request"
  - source: ".sspec/changes/<change-dir>"
    type: "prev-change"
    note: "Follow-up to <change-name>."
-->

# improve-cli-interaction

## Problem Statement

当前 `sprout new <command>` 的核心路径可用，但交互与输入通道存在 5 个高频缺陷，导致首次使用、Agent 代用与脚本调用都不够顺手：

1. **缺参时只报错不接住用户**：例如直接执行 `sprout new issue`，当前仅返回 `Missing required inputs`，没有引导用户进入交互补全
2. **交互提示信息过少**：prompt 未稳定展示字段说明、默认值含义、必填/可选语义，用户需要回看 manifest 才能理解输入
3. **交互流程缺少安全边界**：若自动进入交互，必须确保仅在 TTY 中发生；否则 Agent / bash / CI 容易卡在等待输入
4. **交互前后缺少摘要确认**：正式写文件前看不到本次输入与输出概览，难以及时发现误填或目标路径异常
5. **复杂输入缺少结构化入口**：当前主要依赖 `key=value`，虽然适合简短参数，但对空格、长文本和复杂 shell quoting 不够稳，尤其不利于 Agent 可靠调用

这些问题不会阻断功能，但会显著增加认知负担和试错次数，尤其影响“知道要执行哪个命令，但不想记全参数”的常见场景，以及 Agent 在非交互环境下的稳定执行。

## Proposed Solution

### Approach

采用“**渐进引导 + 多输入通道**”的方案：保留 `sprout new <command> key=value...` 的直接执行能力，同时补上两类增强能力：

1. **TTY 感知的交互引导**：仅当 stdin/stdout 为 TTY 时，缺参才引导用户进入一个可取消的交互补全流程；非交互环境保持立即失败，避免 Agent / bash 卡住
2. **结构化输入入口**：新增 `--json` 与 `--json-file`，让 Agent 和脚本可以稳定传入复杂输入对象，减少 shell quoting 问题

交互补全不直接强制开始，而是先输出缺失字段与说明，再询问是否进入交互模式；用户可以明确选择进入或取消，避免被意外拉进 prompt。进入交互后，每个字段 prompt 都显示更完整的上下文；最终仅在交互模式下增加一次简短确认，确认后才真正写文件。

输入合并策略上，`--json` / `--json-file` 提供基础输入，`pairs` / `--set` 作为覆盖层，既保证结构化输入的稳定性，也保留命令行临时覆盖的灵活性。同时统一改进错误提示与命令发现提示，让非交互路径在失败时也给出下一步行动，而不是只返回底层校验信息。

### Key Change

**Feat A: 仅在 TTY 中引导进入交互补全**
- 当 `sprout new <command>` 缺少必填输入时，CLI 先判断当前是否为 TTY
- 仅在 TTY 中展示缺失字段、字段说明、可执行示例，并询问是否进入交互模式
- 非 TTY 环境保持立即失败；显式 `-i` 但无 TTY 时，返回明确错误而非等待输入
- 增加 `--no-input`，允许用户/Agent 显式禁止任何交互

**Fix B: 交互输入可中止且必填约束正确**
- 交互模式支持显式取消（如输入 `q` / `quit` / `exit`，或 `Ctrl+C`）
- 必填字符串字段不能接受空白值；空输入只在“有默认值”或“非必填”时通过
- 取消时输出一致的中止提示，而不是栈追踪或静默异常

**Feat C: 新增结构化输入入口**
- 新增 `--json '{...}'` 与 `--json-file path.json`，接受 JSON object 作为输入源
- `--json` / `--json-file` 仅支持与现有 schema 对应的标量值（string/number/enum），不支持嵌套对象/数组
- 输入合并优先级：JSON 输入为基础层，`pairs` / `--set` 为覆盖层
- 为 Agent 文档与提示明确推荐 `--json` / `--json-file` 作为复杂输入入口

**Feat D: Prompt 与错误提示信息升级**
- prompt 中稳定展示：字段名、描述、类型约束、可选值、默认值、是否必填
- 未知命令时除了列出可用命令，还提供相近命令建议
- 参数错误时给出明确 next step（示例、`-i`、`--json`、或交互入口）

**Feat E: 仅交互模式下增加执行前确认摘要**
- 用户通过交互补全输入后，CLI 在写文件前展示简洁摘要：命令名、输入值、冲突策略、将要生成的路径
- 用户确认后执行；取消则不写文件
- 非交互快速路径保持无确认步骤

### Scope Summary

| File | Change |
|------|--------|
| `sprout/cli.py` | 调整 `new` 命令主流程，接入 TTY 判断、`--no-input`、`--json`、`--json-file`、交互确认、摘要输出、统一中止处理 |
| `sprout/core.py` | 增强输入收集逻辑，支持 JSON 输入解析/合并、丰富 prompt 元信息、取消语义、缺失字段信息与命令建议 |
| `sprout/models.py` | 如需要，新增交互/输入源相关的数据结构或异常 |
| `tests/` | 新增或扩展 CLI / core 测试，覆盖 TTY/非 TTY 分支、JSON 输入、取消、必填校验、摘要确认、错误提示 |
| `README.md` | 更新 `sprout new` 使用示例，补充 Agent 推荐输入方式与交互边界说明 |

### Design Reference

→ 详细技术设计见 [design.md](./design.md)
