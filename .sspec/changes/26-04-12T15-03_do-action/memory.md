# Memory: do-action

**Updated**: <!-- ISO timestamp, minute precision -->

## Git Baseline (Immutable)
<!-- Captured during `sspec change new` before any change files are written.
This section records the change starting point in git and MUST NOT be edited or refreshed later. -->

- Captured: before change file creation
- Repository: `H:/SrcCode/playground/sprout-cli`
- Branch: `main`
- HEAD: `08332218033bd8e64fd376c658887703d717a425`
- Worktree: `dirty`
- Status Snapshot: raw `git status --short --branch` output

```text
## main...origin/main
?? .env
?? .sspec/requests/
```

## State
- 当前处于 Review gate：实现、测试、文档与 runtime 验证已完成，等待用户评审结果。
- 下一步：根据用户反馈进入接受 / 小修 / 修订分支。

## Key Files
- `.sspec/requests/26-04-12T14-53_do-action.md` — 原始需求，提出 action、asset 引用与模板 shell 的讨论点。
- `.sspec/changes/26-04-12T15-03_do-action/spec.md` — 本次变更的问题定义、范围与关键决策。
- `.sspec/changes/26-04-12T15-03_do-action/design.md` — `ref` / `actions` / action context / shell 边界的技术设计。
- `sprout/core.py` — manifest 解析、渲染、计划与执行主链路；action 功能的主要接入点。
- `sprout/models.py` — 需要扩展 AssetSpec / CommandSpec 及 action 相关模型。
- `sprout/cli.py` — `sprout new` 的输出、dry-run 与 post-action 执行串接点。

## Knowledge
- [2026-04-12T15:08+08:00] [Decision] 用户偏好：架构上预留 phase 扩展，但当前只实现 post-action。
- [2026-04-12T15:08+08:00] [Decision] 用户偏好：资产引用采用具名 `ref`，而不是数组下标引用。
- [2026-04-12T15:08+08:00] [Decision] 用户偏好：action 同时支持 shell 字符串与 argv 数组，但设计上推荐 argv。
- [2026-04-12T15:08+08:00] [Rejected] 暂不采用 `{{!command}}` 模板内 shell 求值；先将副作用集中到 action 机制。
- [2026-04-12T15:25+08:00] [Decision] 用户确认：允许在后续 asset 中引用前面已定义的 asset ref，但仅允许 backward refs。
- [2026-04-12T15:25+08:00] [Decision] 用户确认：assets 作用域要求显式后缀，推荐 `assets.<ref>.rel_path`；actions 作用域允许裸 `assets.<ref>`，默认表示绝对路径。
- [2026-04-12T15:25+08:00] [Decision] 用户确认：路径类变量统一渲染为 `/` 分隔符。
- [2026-04-12T15:25+08:00] [Decision] 用户要求把随机内置变量纳入本次变更，并采用命名空间语法 `rand.str` / `rand.num`。
- [2026-04-12T15:51+08:00] [Decision] Review revision 001：按用户要求移除 TOML 支持，项目运行时格式收缩为 YAML/YML/JSON。

## Milestones
- [2026-04-12T15:08+08:00] 已创建 change `26-04-12T15-03_do-action`，完成首轮 clarify + design 草案并等待用户 gate 确认
- [2026-04-12T15:25+08:00] 根据用户反馈更新 design：增加 asset backward refs、显式 rel/abs 后缀、统一 `/` 路径字符串、纳入 `rand.*` 内置变量
- [2026-04-12T15:43+08:00] 已完成实现与验证：26 个单测通过，并在 `temp/runtime-action-test` 中完成 `sprout doctor` + `sprout new` 运行时验证
- [2026-04-12T15:51+08:00] 已完成 revision 001：删除 TOML 支持，测试全绿，并在 `temp/runtime-action-test-no-toml` 中完成无 TOML runtime 验证
