# Memory: improve-usability

**Updated**: 2026-04-11T17:39

## Git Baseline (Immutable)
<!-- Captured during `sspec change new` before any change files are written.
This section records the change starting point in git and MUST NOT be edited or refreshed later. -->

- Captured: before change file creation
- Repository: `H:/SrcCode/playground/sprout-cli`
- Branch: `main`
- HEAD: `481b4063c869dae7c5eacb3c9498bf4eb931bd8c`
- Worktree: `dirty`
- Status Snapshot: raw `git status --short --branch` output

```text
## main
M  .gitignore
M  AGENTS.md
M  pyproject.toml
```

## State

Design 已确认，进入 Plan 阶段。正在编写 tasks.md 执行计划。

## Key Files

- `sprout/cli.py` — CLI 入口，需添加 --dry-run 参数
- `sprout/core.py` — 核心逻辑，包含生成计划构建和应用
- `README.md` — 用户文档，需更新依赖说明

## Knowledge

- [2026-04-11T17:35] Decision: 采用模板外部化策略，将 `scaffold.py` 中硬编码的 SKILL 文档和示例命令包移至 `sprout/templates/` 目录。理由：提高可维护性、支持用户自定义、与 sprout 设计理念一致。
- [2026-04-11T17:35] Constraint: 模板目录必须在打包时包含在 wheel 中，需配置 `pyproject.toml` 的 `[tool.hatch.build.targets.wheel]`。
<!-- 不属于 spec/design/tasks/revisions 的独有信息。
只放 spec/design 没覆盖的：被否决的方案、隐性知识、用户偏好、"这个 API 有坑"。
格式：- [timestamp] [Type] content
Types: Decision, Constraint, Gotcha, Rejected
项目级发现 → ALSO append to project.md Notes。
过时项标注时间戳，不要静默删除。 -->

## Milestones

- [2026-04-11T17:39] Plan 阶段完成，分解为 5 个阶段 29 个任务，准备开始实现
