---
change: "builtin-command-bootstrap"
created: 2026-04-12T17:27:13
---

# Design: builtin-command-bootstrap

<!-- 本文件记录技术设计详情。创建条件：
变更涉及新接口定义、数据模型变更、或架构逻辑改动。
简单 bugfix/文案修改不需要此文件。 -->

<!-- QUALITY BAR (不可违反):
用半结构化、形式化的表达替代平铺直叙的纯文本。
核心目标：提高信息密度，降低不确定性，提高用户理解效率。
一句话：能展示的不要叙述 (show, don't describe)。

常见手段 (非穷举):
- typed code block: 接口、类型、Schema、配置、prompt...
- ASCII diagram: 调用链、状态机、模块树、内容大纲...
- table: before/after 对比、选项权衡、scope 映射...
- labeled items: 多项变更标注 (Fix A / Feat B / Step 1...)
- 伪代码、决策树、约束列表等同样有效

Anti-pattern:
  ❌ "我们将添加一个接受 X 返回 Y 的函数"
  ✅ `def process(x: Input) -> Output: ...`

  ❌ "请求先经过 A 模块处理，然后传递给 B"
  ✅ request → A.validate() → B.process() → response
-->

<!-- 按变更性质组织本文档。没有固定章节要求。
以下是不同类型变更的参考组织方式 (选用，不强制):

Feature/Bugfix  → 接口签名 + 行为流程 + 数据模型
Refactor        → Before/After 结构对比 + 迁移步骤
文档/模板       → 内容大纲 + 章节层级
Prompt/规则     → Before/After 示例 + 决策逻辑
配置/Schema     → Schema 定义 + 迁移路径 + 兼容性策略
-->

## Naming Decision

| Candidate | Pros | Cons | Decision |
|-----------|------|------|----------|
| `__new__/` | 直接对应 `sprout new` 的生成语义；与“新增 command 包”更贴近 | 名称略抽象，但可通过文档解释 | ✅ 采用 |
| `__template__/` | 看起来像模板目录 | 易与 command 包内部模板文件混淆；用户可能误以为这里放通用渲染模板而不是 command package | ❌ 不采用 |

## CLI surface

```text
sprout builtin <name>
sprout buildin <name>   # alias
```

```python
# cli dispatch shape
if args.command in {"builtin", "buildin"}:
    return _run_builtin(args)
```

Behavior:
- `name` 必填，作为 command package 目录名与默认 manifest `name`
- 若 `.sprout/commands/` 存在而 `.sprout/__new__/` 不存在，先迁移旧目录到新目录
- 若两者同时存在，先把旧目录中缺失的子目录合并到新目录；同名子目录保留两边，后续由 runtime registry 按 command name 检测 conflict
- 最终仅生成 `.sprout/__new__/<name>/manifest.yaml`
- 若目标 manifest 已存在，保持幂等：报 skipped/已存在，不覆盖用户文件

## Directory resolution model

```python
PREFERRED_COMMANDS_DIR = "__new__"
LEGACY_COMMANDS_DIR = "commands"

@dataclass(slots=True)
class AuthoringDirs:
    preferred: Path          # .sprout/__new__
    legacy: Path             # .sprout/commands
    discover_order: list[Path]
```

### Write path rule

```text
write/init/builtin
  → ensure .sprout exists
  → migrate_or_merge(commands -> __new__)
  → write into .sprout/__new__/
```

### Read path rule

```text
load_registry
  → inspect .sprout/__new__/ first
  → inspect .sprout/commands/ second
  → aggregate all package dirs
  → same command.name => existing conflict reporting
```

## Migration behavior

```text
Case A: only commands/ exists
  commands/  ──rename──>  __new__/

Case B: both exist
  commands/foo (missing in __new__)   ──move──> __new__/foo
  commands/bar (already in __new__)   ──keep both roots for runtime detection
  commands/ empty after moves         ──remove

Case C: only __new__/ exists
  no-op
```

Constraints:
- 只移动 command package 子目录，不尝试深度合并同名 package 内部文件
- 同名 package 若同时存在于新旧目录，不自动重命名、不覆盖
- 迁移必须保持在 `.sprout/` 内部

## Builtin manifest template outline

```yaml
name: <name>
description: Describe what this command generates

# Optional per-command conflict override.
# If omitted, sprout uses `.sprout/config.yaml`.
# conflict: fail

inputs:
  - name: name
    type: string
    description: Primary identifier used in generated paths

assets:
  - type: dir
    path: output
    ref: output_dir

  - type: file
    path: "{{assets.output_dir.rel_path}}/{{name}}.md"
    template: template.md
```
```

Actual builtin output in this change is **manifest only**; template reference remains commented example text rather than creating `template.md`.

## Affected docs/content

```text
README.md
sprout/docs/user-guide.md
sprout/docs/command-authoring-guide.md
sprout/templates/profiles/minimal.json
sprout/templates/profiles/docs.json
```

Required updates:
- `.sprout/commands/<name>/...` → `.sprout/__new__/<name>/...`
- 新增 `sprout builtin <name>` 用法
- 标注兼容读取旧版 `commands/`
