# Memory: improve-cli-interaction

**Updated**: <!-- ISO timestamp, minute precision -->

## Git Baseline (Immutable)
<!-- Captured during `sspec change new` before any change files are written.
This section records the change starting point in git and MUST NOT be edited or refreshed later. -->

- Captured: before change file creation
- Repository: `H:/SrcCode/playground/sprout-cli`
- Branch: `perf/cli-usage`
- HEAD: `579653f31256cad7c2777febe1f5aed8714b0d20`
- Worktree: `clean`
- Status Snapshot: raw `git status --short --branch` output

```text
## perf/cli-usage
```

## State

用户已接受本次改动，change 已完成。下一步执行 git commit，并将 change 归档。

## Key Files

- `sprout/cli.py` — `new` 命令主流程、参数定义、TTY 检测、确认与错误输出
- `sprout/core.py` — 输入解析/校验/交互收集的核心逻辑
- `sprout/models.py` — 若需新增交互取消或输入源相关异常/数据结构
- `README.md` — 用户侧交互说明与 Agent 推荐用法
- `tests/` — 需要新增 JSON 输入、非 TTY、取消与确认测试

## Knowledge

- [2026-04-11T21:06] [Decision] 自动交互引导仅在 `stdin` 和 `stdout` 均为 TTY 时启用；非 TTY 缺参必须立即失败，避免 Agent/bash 卡住。
- [2026-04-11T21:06] [Decision] 新增 `--no-input` 作为显式禁交互开关，与 TTY 保护一起形成双保险。
- [2026-04-11T21:06] [Decision] 不引入动态 `--name value` 参数解析；本次新增 `--json` 与 `--json-file` 作为 Agent/脚本的结构化输入入口。
- [2026-04-11T21:06] [Constraint] `--json` / `--json-file` 仅接受顶层 object，且 value 仅支持可映射到现有 schema 的标量值；不支持嵌套对象或数组。
- [2026-04-11T21:06] [Decision] 输入合并优先级为：JSON 基础层 → 位置参数 `pairs` → `--set` 覆盖层 → 交互补全缺失值。
- [2026-04-11T21:31] [Decision] 默认 example 从 `change` 调整为 `task`，避免与 `.sspec` 术语产生产品层面的概念混淆。
- [2026-04-11T21:31] [Decision] `AGENTS.md` 开头补充项目背景，明确 `sprout` 是产品，`.sspec` 是仓库内开发流程工具。

## Milestones

- [2026-04-11T21:06] 设计补充 TTY 保护与 JSON 输入方案，Plan 完成并拆分为 4 个阶段 15 个任务
- [2026-04-11T21:22] 实现完成：新增 JSON 输入、TTY 保护、交互确认与改进提示；定向测试与 temp 手测通过
- [2026-04-11T21:31] Review 小修完成：example 改为 task，AGENTS.md 背景补充完成
- [2026-04-11T21:43] 用户确认通过，change 标记为 DONE，准备 commit 与 archive
