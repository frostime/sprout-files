# Memory: builtin-command-bootstrap

**Updated**: <!-- ISO timestamp, minute precision -->

## Git Baseline (Immutable)
<!-- Captured during `sspec change new` before any change files are written.
This section records the change starting point in git and MUST NOT be edited or refreshed later. -->

- Captured: before change file creation
- Repository: `H:/SrcCode/playground/sprout-cli`
- Branch: `main`
- HEAD: `cc3cd64285735068006ebce10429cd0588678af3`
- Worktree: `dirty`
- Status Snapshot: raw `git status --short --branch` output

```text
## main...origin/main
?? .sprout/
```

## State
实现已完成，已通过单元测试与 runtime smoke test；下一步等待用户 review。
如用户接受，则进入 review 完成态；若有反馈，再按当前 change 继续修订。

## Key Files
- `sprout/cli.py` — 当前 CLI 子命令入口；需新增 builtin/buildin 分发
- `sprout/core.py` — command registry 加载逻辑；需兼容 `__new__/` 与 `commands/`
- `sprout/scaffold.py` — init 与脚手架生成逻辑；需承载目录迁移和 manifest 模板生成
- `sprout/docs/command-authoring-guide.md` — authoring 规则与路径文案来源
- `tests/test_init.py` — init 路径与脚手架输出断言
- `tests/test_core.py` / `tests/test_cli_interaction.py` — registry 兼容与 CLI 行为测试

## Knowledge
- [2026-04-12T17:28+08:00] [Decision] CLI 规范名采用 `builtin`，同时保留 `buildin` 作为兼容别名，以兼顾自然拼写和用户原始请求。
- [2026-04-12T17:28+08:00] [Decision] 新默认目录采用 `.sprout/__new__/`，原因是它与 `sprout new` 的用户心智更贴近，且比 `__template__/` 更不容易和包内模板文件混淆。
- [2026-04-12T17:28+08:00] [Constraint] 用户要求保留对旧版 `.sprout/commands/` 的读取兼容，并倾向自动迁移/合并而非要求手动重命名。
- [2026-04-12T17:28+08:00] [Constraint] builtin 这次只生成 `manifest.yaml`，不额外落盘模板文件。
- [2026-04-12T17:43+08:00] [Decision] registry 发现顺序为 `__new__/` 后 `commands/`；若 command name 重复，继续沿用既有 conflict 检测，不做静默覆盖。
- [2026-04-12T17:43+08:00] [Decision] 迁移逻辑只移动不重名的 legacy command package；同名 package 不做深度文件合并。

## Milestones
- [2026-04-12T17:28:10+08:00] 创建 change `26-04-12T17-27_builtin-command-bootstrap`，完成 spec/design 草案并等待 @align gate。
- [2026-04-12T17:43:31+08:00] 完成 builtin/buildin 命令、`__new__/commands` 双目录兼容、authoring 文档更新、38 项测试通过与 runtime smoke test。
