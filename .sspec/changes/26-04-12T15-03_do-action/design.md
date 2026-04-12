---
change: "do-action"
created: 2026-04-12T15:03:23
---

# Design: do-action

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

## 1. Manifest Schema Proposal

```yaml
name: scanfold
inputs:
  - name: name
    type: string

assets:
  - type: dir
    path: projects/{{name}}
    ref: project_dir

  - type: file
    path: "{{assets.project_dir.rel_path}}/README.md"
    content: "# {{name}}\n"
    ref: readme

  - type: file
    path: "tmp/{{rand.str:8}}.md"
    content: "temp note\n"

actions:
  - phase: post
    run: ["git", "init"]
    cwd: "{{assets.project_dir}}"

  - phase: post
    shell: "echo created {{assets.readme.abs_path}}"
```

### Proposed typed model

```python
AssetRef = str  # manifest-local unique name, pattern: [A-Za-z_][A-Za-z0-9_]*
ActionPhase = Literal["post"]  # schema shape leaves room for future "pre"

@dataclass(slots=True)
class AssetSpec:
    type: AssetType
    path: str
    template: str | None = None
    content: str | None = None
    ref: str | None = None

@dataclass(slots=True)
class ActionSpec:
    phase: ActionPhase = "post"
    run: list[str] | None = None   # preferred argv form
    shell: str | None = None       # convenience form
    cwd: str | None = None
    description: str = ""

@dataclass(slots=True)
class ExecutedAction:
    index: int
    phase: ActionPhase
    mode: Literal["argv", "shell"]
    command_display: str
    cwd: Path | None
```

## 2. Variable Syntax Proposal

### Extended placeholder grammar

```text
{{name}}                  # existing input / built-in variable
{{assets.project_dir}}    # bare asset ref (action scope only) => abs_path
{{assets.project_dir.abs_path}}
{{assets.project_dir.rel_path}}
{{assets.project_dir.name}}
{{assets.project_dir.parent_abs}}
{{assets.project_dir.parent_rel}}
{{rand.str:10}}
{{rand.num:6}}
```

### Grammar constraints

```text
identifier := [A-Za-z_][A-Za-z0-9_]*
asset-ref   := assets.identifier(.suffix)?
rand-token  := rand.(str|num)(:length)?
length      := positive integer
```

### Path separator policy

All path-like variables render as strings using `/` separators on every platform.
Internally, runtime still converts them back to `Path` objects before filesystem/subprocess use.

## 3. Runtime Flow

```text
sprout new
  → load manifest
  → validate inputs
  → render asset paths/content
  → resolve conflicts / final paths
  → apply generation plan
  → build action context from generated results
  → execute post actions in declaration order
  → print generated items + action results
```

### Dry-run flow

```text
sprout new --dry-run
  → build generation plan
  → preview action command + cwd after interpolation
  → DO NOT execute actions
```

## 4. Asset / Action Context Contract

### Asset scope vs action scope

| Scope | Can access | Bare `{{assets.ref}}` meaning |
|------|------------|-------------------------------|
| `assets[*].path` rendering | inputs + built-ins + previous asset refs | forbidden |
| action rendering (`run` args / `shell` / `cwd`) | inputs + built-ins + all final asset refs | `assets.<ref>.abs_path` |

### Available asset suffixes

```text
assets.<ref>.abs_path
assets.<ref>.rel_path
assets.<ref>.name
assets.<ref>.parent_abs
assets.<ref>.parent_rel
```

Rules:
- In asset path templates, only backward refs are allowed
- In asset path templates, reference MUST be explicit (`.rel_path`, etc.)
- In action templates, bare `assets.<ref>` is allowed and means `.abs_path`
- `rel_*` values use project-root-relative `/` paths
- `abs_*` values use absolute `/` paths

### Why named refs, not indexes

| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| `assets.0.path` | easiest to implement | 与 assets 顺序耦合；重构 manifest 易破坏引用；可读性差 | Reject |
| `ref: project_dir` + `assets.project_dir.path` | 语义稳定、易读、适合长期维护 | 需要唯一性校验 | Accept |

## 5. Action Validation Rules

| Rule | Behavior |
|------|----------|
| `actions` optional | absent = no actions |
| `phase` only `post` | others fail validation for now |
| exactly one of `run` / `shell` | both or neither = validation error |
| `run` must be non-empty list[str] | otherwise validation error |
| `cwd` optional | if present, render after generation and must stay inside project root |
| `ref` optional | if present, must be unique and match variable-name pattern |
| action interpolation may only use known vars | unknown variable = validation error during planning |
| asset path interpolation may only use previous refs | forward/self/cycle references fail validation |
| bare `assets.<ref>` in asset paths | validation error |
| `rand.str` / `rand.num` length default | fixed default (recommended 8) when omitted |
| `rand.*:len` length | must be positive integer within bounded max |

## 6. Execution / Failure Semantics

```text
for action in post_actions:
  render command + cwd
  run subprocess
  if exit_code != 0:
    stop immediately
    raise GenerationError with action index + command summary
```

### Chosen semantics

- 串行执行，保持声明顺序
- 任一 action 失败即停止后续 action
- **不回滚**已生成文件；sprout 保持“生成器”而非事务系统
- stdout/stderr 首版沿用简单透传/摘要策略即可，不先设计复杂日志模型

## 7. Built-in Random Tokens

### Proposed semantics

| Token | Charset | Example |
|-------|---------|---------|
| `{{rand.str}}` | `[0-9A-Za-z]` | `a8K2mP0Q` |
| `{{rand.str:10}}` | `[0-9A-Za-z]` | `F0ab91KqZ2` |
| `{{rand.num}}` | `[0-9]` | `48312057` |
| `{{rand.num:6}}` | `[0-9]` | `481203` |

### Recommendation

- 语法采用 `rand.str` / `rand.num`，不要使用 `random-str` 这类连字符形式
- 默认长度建议为 `8`
- 每次 placeholder 出现都独立生成一次，不做“同 token 文本自动复用”
- 如用户需要复用同一随机值，未来再设计 `capture` / named generated variable 机制

## 8. Shell-in-Template Decision

| Candidate | Benefit | Cost / Risk | Decision |
|-----------|---------|-------------|----------|
| `{{!command}}` in templates | 极强表达力 | 模板有副作用；难做 dry-run；变量嵌套/转义复杂；doctor 难静态校验 | Reject for now |
| actions only | 边界清晰；副作用集中；易解释 | 模板内不能直接嵌入命令结果 | Accept |

### Future-compatible note

若未来确实需要动态值，优先考虑**显式新阶段**而非模板内求值，例如：

```yaml
actions:
  - phase: pre
    ref: git_user
    capture: ["git", "config", "user.name"]
```

再将捕获值注入后续模板上下文。这样比 `{{!command}}` 更可控、更可测试。

## 9. CLI Output Preview

```text
Executed command: scanfold
Conflict policy: fail
  + CREATE projects/demo
  + CREATE projects/demo/README.md
  > ACTION [post] git init (cwd=projects/demo)
```

Dry-run:

```text
[DRY-RUN] Executed command: scanfold
[DRY-RUN] Conflict policy: fail
[DRY-RUN]   + CREATE projects/demo
[DRY-RUN]   + CREATE projects/demo/README.md
[DRY-RUN]   > ACTION [post] git init (cwd=projects/demo)
```

## 10. Affected Interfaces

```python
def _parse_asset_spec(raw: Any, manifest_path: Path, index: int) -> AssetSpec: ...
def _parse_action_spec(raw: Any, manifest_path: Path, index: int) -> ActionSpec: ...
def build_asset_render_context(...) -> dict[str, Any]: ...
def build_action_context(values: dict[str, Any], generated: list[GeneratedItem], ref_map: dict[str, Path], root: Path) -> dict[str, Any]: ...
def render_text(template: str, context: dict[str, Any], *, scope: Literal["base", "asset", "action"] = "base") -> str: ...
def plan_actions(command: CommandSpec, context: dict[str, Any], root: Path) -> list[ExecutedAction]: ...
def execute_actions(actions: list[ExecutedAction], *, dry_run: bool = False) -> None: ...
def generate_random_token(kind: Literal["str", "num"], length: int) -> str: ...
```

## 11. Boundary / Non-goals

- 本次不支持 `pre` action 的真实执行
- 本次不支持 action 产出捕获并回注模板变量
- 本次不支持模板内 shell 求值
- 本次不引入跨平台 shell 抽象层；`shell` 形态遵循当前运行平台默认行为
