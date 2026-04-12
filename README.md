# sprout CLI (v0.1)

`sprout` 是一个项目内模板驱动的文件/目录生成 CLI，面向 Agent 协同开发场景。

## 核心特性

- 发现规则：从当前目录向上查找首个 `.sprout/`（类似 `.git`）
- 命令包目录：`.sprout/commands/<command>/`
- 默认 authoring 格式：YAML（便于注释、示例和值说明）
- 输入模式：支持 `key=value`、`--json`、`--json-file`；TTY 下缺参可引导进入交互
- 基础类型：`string` / `number` / `enum`（`number` 支持可选 `min/max`）
- 插值语法：支持输入变量、时间变量、`assets.<ref>.<suffix>`、`rand.str[:N]` / `rand.num[:N]`（仅纯文本替换，不支持逻辑流）
- 可选 post-action：生成完成后执行 `run: [...]` 或 `shell: "..."`
- 冲突策略：`fail` / `overwrite` / `skip` / `rename`
- `init` 支持自定义骨架、可选示例命令包，并生成项目内 `sprout-authoring` Skill 文档
- 运行时兼容 `yaml` / `yml` / `json` 配置与 manifest

## 快速开始

```bash
# 0) 可选：安装 YAML 支持（推荐）
uv add --optional yaml
# 或使用 pip: pip install pyyaml

# 1) 初始化
sprout init --with-examples

# 2) 查看命令
sprout list --all

# 3) 执行命令（默认参数模式，使用 = 连接键值）
sprout new issue name=my-task type=bug

# 4) 结构化输入（适合 Agent / 长文本 / 含空格值）
sprout new issue --json '{"name":"my task","type":"bug"}'
sprout new issue --json-file ./inputs.json

# 5) 交互模式
sprout new issue -i
# 或者直接 `sprout new issue`
# 若当前终端是 TTY 且缺少必填参数，sprout 会先询问是否进入交互模式
# 交互中可输入 q / quit / exit 取消

# 6) 预览模式（不实际创建文件）
sprout new issue name=test type=feat --dry-run
```

## 命令

```bash
sprout init [--profile minimal|docs] [--profile-file ./profile.json] [--with-examples]
sprout list [--all]
sprout doctor
sprout new <command> [key=value ...] [--json '{...}' | --json-file ./inputs.json] [--set key=value] [-i|--interactive] [--no-input] [--conflict fail|overwrite|skip|rename]
```

## `.sprout/` 结构

```text
.sprout/
  config.yaml
  commands/
    issue/
      manifest.yaml
      issue.md
  skills/
    sprout-authoring/
      SKILL.md
```

## 如何填写 `.sprout/config.yaml`

```yaml
# sprout project defaults
version: 1

# Default conflict policy for generated assets.
# Allowed: fail | overwrite | skip | rename
conflict: fail
```

字段说明：
- `version`：整数，当前固定为 `1`
- `conflict`：项目级默认冲突策略；可选 `fail` / `overwrite` / `skip` / `rename`

## 如何填写 `manifest.yaml`

```yaml
name: issue
description: Create issue

# Optional per-command conflict override.
# If omitted, sprout uses `.sprout/config.yaml`.
conflict: fail

inputs:
  - name: name
    type: string
    required: true
    description: Issue slug

  - name: type
    type: enum
    enum:
      - bug
      - feat
      - refactor
    default: bug
    description: Issue category

  - name: priority
    type: number
    required: false
    min: 1
    max: 5
    default: 3
    description: Optional priority

assets:
  - type: dir
    path: issues
    ref: issues_dir

  - type: file
    path: "{{assets.issues_dir.rel_path}}/{{YY}}-{{MM}}-{{DD}}_{{name}}-{{rand.str:6}}.md"
    template: issue.md
    ref: issue_file

actions:
  - phase: post
    run: ["git", "status"]
    cwd: "{{project.root}}"
```

### 字段说明

#### `inputs[*]`
- `name`：必填，且在同一命令内唯一
- `type`：`string` / `number` / `enum`
- `required`：可选，默认 `true`
- `description`：可选，但建议填写，方便 Agent 理解用途
- `default`：可选默认值
- `enum`：当 `type: enum` 时必填
- `min` / `max`：仅 `number` 类型可用

#### `assets[*]`
- `type`：`dir` 或 `file`
- `path`：项目内相对路径
- `template`：文件资产引用的模板文件，路径相对当前命令目录
- `content`：简单文件可直接内联内容；与 `template` 二选一即可
- `ref`：可选资源引用名，供后续 asset 或 action 使用；同一命令内必须唯一

#### `actions[*]`
- `phase`：当前仅支持 `post`
- `run`：推荐写法，参数数组形式执行命令
- `shell`：便捷写法，执行单条 shell 命令
- `cwd`：可选工作目录；支持模板插值，且必须仍在项目根目录内
- `run` / `shell` 必须二选一

## 变量上下文

除了输入变量，内置时间变量：

- `YYYY`, `YY`, `MM`, `DD`
- `hh`, `mm`, `ss`
- `date`, `time`, `datetime`, `timestamp`

还支持：

- `project.root`：项目根目录绝对路径
- `project.root_name`：项目根目录名
- `rand.str` / `rand.str:N`：随机字母数字串，默认长度 `8`
- `rand.num` / `rand.num:N`：随机数字串，默认长度 `8`

### Asset 引用变量

当 asset 定义了 `ref` 后，可在后续 asset 与 actions 中使用：

- `assets.<ref>.abs_path`
- `assets.<ref>.rel_path`
- `assets.<ref>.name`
- `assets.<ref>.parent_abs`
- `assets.<ref>.parent_rel`

规则：

- 在 `assets[*].path` 中，只允许引用**前面**已定义的 `ref`
- 在 `assets[*].path` 中，必须显式写后缀，推荐 `{{assets.<ref>.rel_path}}`
- 在 `actions[*]` 中，允许直接写 `{{assets.<ref>}}`，默认等价于 `{{assets.<ref>.abs_path}}`
- 所有路径变量字符串统一使用 `/` 分隔符

## 冲突策略说明

当生成的文件或目录已存在时，sprout 会根据冲突策略处理：

- `fail`（默认）：报错并停止
- `skip`：跳过已存在的文件
- `overwrite`：覆盖已存在的文件
- `rename`：重命名新文件（添加 `_02`、`_03` 等后缀）

**目录特殊处理**：目录被视为容器而非内容，已存在的目录会自动复用（REUSE），不受冲突策略影响。只有文件冲突才会应用冲突策略。

示例：
```bash
# 第一次执行
sprout new issue name=test type=bug
# 输出：
#   + CREATE issues
#   + CREATE issues/26-04-11_test.md

# 第二次执行（目录已存在）
sprout new issue name=another type=feat
# 输出：
#   = REUSE issues              # 目录自动复用
#   + CREATE issues/26-04-11_another.md

# 第三次执行（文件冲突）
sprout new issue name=another type=feat
# 输出：
#   Error: Target already exists: issues/26-04-11_another.md
#   Hint: Use --conflict=skip or --conflict=overwrite
```

## Action 输出示例

```bash
sprout new issue name=test --dry-run
# 输出：
# [DRY-RUN] Executed command: issue
# [DRY-RUN] Conflict policy: fail
# [DRY-RUN]   + CREATE issues
# [DRY-RUN]   + CREATE issues/26-04-12_test-a1B2c3.md
# [DRY-RUN]   > ACTION [post] git status (cwd=.)
```

## 交互与 Agent 调用建议

- **TTY 下缺参**：sprout 会先说明缺了哪些字段，再询问是否进入交互模式
- **非 TTY 下缺参**：sprout 不会等待输入，而是直接失败，避免脚本或 Agent 卡住
- **显式 `-i` 但非 TTY**：会报错 `Interactive mode requires a TTY`
- **复杂输入**：优先使用 `--json` 或 `--json-file`，比 shell 中拼接 `key=value` 更稳
- **临时覆盖**：可在 `--json` / `--json-file` 基础上再用 `--set key=value` 覆盖字段

## Agent authoring 建议

如果让 Agent 帮你写 `.sprout`，先让它读取：

- `.sprout/skills/sprout-authoring/SKILL.md`

然后先对齐：
1. 命令目的
2. 输入字段及类型
3. 输出文件/目录
4. 冲突策略

不要一上来直接让 Agent 写 manifest。

## 常见问题

- **找不到项目模板根**：确认当前目录或父目录存在 `.sprout/`
- **命令不可用**：执行 `sprout doctor` 检查 invalid/conflict 报告
- **YAML 无法读取**：安装 `PyYAML`，或继续使用 TOML / JSON
