---
name: do-action
status: REVIEW
change-type: single
created: 2026-04-12 15:03:23
reference:
- source: .sspec/requests/26-04-12T14-53_do-action.md
  type: request
  note: Linked from request
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

# do-action

## Problem Statement
当前 `sprout` 的命令清单只支持 `inputs` + `assets`，导致“创建骨架后顺手完成初始化动作”这一类场景仍需用户手工执行，削弱了它作为通用骨架生成器的闭环能力。典型例子是：生成项目目录后仍要手动进入目录执行 `git init`、初始化工具链或触发本地脚本。

同时，现有资产模型缺少稳定的“已生成资源引用名”。一旦后续能力要消费生成结果（尤其在 `rename` / `skip` / `overwrite` 等冲突策略下），就无法用可读、可维护的方式引用“最终实际落地”的文件/目录路径。

## Proposed Solution

### Approach
为 manifest 增加两类能力：

1. **资产命名引用**：在 `assets[*]` 上增加可选 `ref` 字段，为后续动作提供稳定名字，而不是依赖数组下标。
2. **后置动作 `actions`**：在资源创建成功后执行声明式动作。配置结构预留 `phase`，但首版只支持 `post`，避免一次性引入 pre/post 双阶段复杂度。
3. **扩展变量语法**：把模板变量从“仅简单标识符”扩展到受控命名空间，支持 `assets.<ref>` / `assets.<ref>.<suffix>` / `rand.<kind>:<len>` 等形式。

动作执行采用“两种声明方式并存”的策略：推荐 `argv` 风格（YAML 中写成字符串数组）以获得更稳的跨平台与转义行为；同时允许单条 shell 字符串，满足简单场景的易写性。动作上下文可引用**实际生成结果**，因此在重命名或复用场景中拿到的仍是最终有效路径。

具名 asset ref 不仅可用于 actions，也可在后续 asset 中进行**向前引用**。为保持语义明确：在 `assets[*].path` 这类“继续拼相对路径”的位置，要求显式使用 `.rel_path`；在 action 中允许裸写 `{{assets.<ref>}}`，默认展开为绝对路径；所有路径类变量字符串统一使用 `/` 分隔符。

本次**不引入** `{{!command}}` 这类模板内动态 shell 求值。模板继续保持“纯声明式渲染”，副作用集中在 action 阶段，保证 dry-run、doctor、变量校验与安全边界仍然清晰可预测。随机字符串能力作为受控内置变量一并纳入本次设计，而不是通过 shell 求值绕过模板系统。

### Key Change
**Feat A: Asset Ref Naming**  
为 `assets[*]` 增加可选 `ref` 字段，要求在单个命令内唯一，并为 action 提供稳定引用入口。拒绝数组下标引用方案，避免模板顺序耦合。

**Feat B: Post Actions with Extensible Phase Shape**  
新增 `actions[*]` 清单，结构中包含 `phase` 字段，首版仅实现 `post` 执行。动作在资源创建成功后、按声明顺序串行运行；dry-run 仅展示不执行。

**Feat C: Scoped Asset Ref Rendering**  
为 `assets.<ref>` 定义分场景语义：在后续 asset 的路径模板中允许向前引用，但必须显式写 `assets.<ref>.rel_path`；在 action 模板中允许裸写 `assets.<ref>`，默认等价于 `assets.<ref>.abs_path`。所有路径字符串统一渲染为 `/` 分隔符。

**Feat D: Built-in Random Tokens**  
新增受控随机内置变量，采用命名空间语法（如 `{{rand.str:10}}`、`{{rand.num:6}}`），用于临时目录/文件命名等场景，避免借助 shell 求值制造动态值。

**Guard E: Keep Templates Declarative**  
明确不支持 `{{!command}}` 模板内命令执行。shell 副作用统一留在 action 机制，减少复杂度与不可预测性。

### Scope Summary
| File | Change |
|------|--------|
| `sprout/models.py` | 扩展 manifest 数据模型，新增 action/asset-ref 相关类型 |
| `sprout/core.py` | 解析/校验 `ref`、扩展变量语法与 `actions`，构建 asset/action 上下文，规划并执行 post action |
| `sprout/cli.py` | 在 `new` 命令中串接 action 执行与输出展示；dry-run 行为补充 |
| `tests/` | 增加 action 解析、asset 向前引用、路径后缀语义、random 变量、dry-run、失败传播等测试 |
| `README.md` | 补充 manifest 新字段、引用语法、random 变量、action 行为与边界说明 |
| `sprout/templates/skill-authoring.md` | 更新作者文档，纳入 `ref`/`actions`/`rand.*` 设计与推荐写法 |

### Design Reference
→ 详细技术设计见 [design.md](./design.md)
