---
name: builtin-command-bootstrap
status: DONE
change-type: single
created: 2026-04-12T17:27:13
reference: null
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

# builtin-command-bootstrap

## Problem Statement
当前新增一个自定义 command 需要手动创建至少 **1 个目录 + 1 个 manifest 文件**，首个 authoring 流程完全依赖手工搭建，导致新用户/Agent 很难快速得到可编辑的起点模板。

同时，默认目录名仍是 `.sprout/commands/`，而用户实际执行入口是 `sprout new <command>`；目录命名与用户心智不一致，且 `commands/` → 新目录名的兼容与迁移行为尚未定义，导致升级后可能出现新旧目录并存、来源不清的问题。

## Proposed Solution

### Approach
引入一个内置脚手架子命令，**规范化创建 command manifest 模板**，让用户可直接运行 `sprout builtin <name>` 生成带完整注释的 `manifest.yaml`。为兼容用户原始表述与更自然的英文拼写，CLI 采用 `builtin` 作为规范名称，同时保留 `buildin` 作为兼容别名。

目录层面，将默认 command authoring 目录从 `.sprout/commands/` 调整为 `.sprout/__new__/`。选择 `__new__/` 而不是 `__template__/`，是因为前者直接对应 `sprout new` 的用户操作语义，后者容易与 command 包内部的模板文件（`template.md`、`issue.md` 等）混淆。运行时继续兼容旧版 `commands/`，并在需要写入或初始化工作区时自动把旧目录提升/合并到 `__new__/`，减少手动迁移成本。

### Key Change
**Feat A: Builtin manifest scaffold command** — 新增 `sprout builtin <name>`（兼容别名 `buildin`），自动创建 `.sprout/__new__/<name>/manifest.yaml`，仅生成 manifest 文件，并内置必要注释作为 authoring 起点。

**Feat B: Preferred authoring directory migration** — 默认写入目录改为 `.sprout/__new__/`；若存在旧版 `.sprout/commands/`，则在初始化/写入路径解析时自动迁移或合并到新目录。

**Compat C: Dual-directory runtime discovery** — 读取 registry 时兼容 `__new__/` 与 `commands/`；若迁移后仍存在 manifest 层面的同名 command，沿用现有 conflict 机制报告，而不是静默覆盖。

**Docs D: User-facing authoring guidance refresh** — 更新 README、内置文档、初始化脚手架文案与示例路径，统一指向 `__new__/` 与新的 builtin 工作流，同时说明旧版 `commands/` 仍被兼容读取。

### Scope Summary
| File | Change |
|------|--------|
| `sprout/cli.py` | 新增 `builtin`/`buildin` 子命令与执行入口 |
| `sprout/core.py` | 抽取/加入 authoring 目录解析、旧目录迁移合并、双目录兼容发现 |
| `sprout/scaffold.py` | `init` 改为创建 `__new__/`，新增内置 manifest 模板生成与目录迁移辅助逻辑 |
| `sprout/templates/` | 新增 command manifest 模板；更新 profile / example 相关文案路径 |
| `sprout/docs/*.md` | 更新 authoring 与 workspace 结构说明 |
| `README.md` | 更新 CLI、目录结构、快速开始说明 |
| `tests/*.py` | 增加 builtin、目录迁移、双目录兼容与 init 路径更新测试 |

### Design Reference
→ 详细技术设计见 [design.md](./design.md)
