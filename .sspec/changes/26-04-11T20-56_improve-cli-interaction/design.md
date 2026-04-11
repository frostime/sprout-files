---
change: "improve-cli-interaction"
created: 2026-04-11T20:56:38
---

# Design: improve-cli-interaction

## UX Flow

```text
Case 1: 完整参数直达
sprout new issue name=abc type=bug
  → parse pairs / --set
  → validate provided inputs
  → build plan
  → execute

Case 2: 结构化输入
sprout new issue --json '{"name":"abc task","type":"bug"}'
sprout new issue --json-file ./inputs.json
  → parse JSON object
  → merge pairs / --set as overrides
  → validate provided inputs
  → build plan
  → execute

Case 3: TTY 中缺少必填参数
sprout new issue
  → detect missing required inputs: [name]
  → confirm current session is TTY
  → print missing-field summary + example
  → ask: Enter interactive mode? [Y/n]
      ├─ yes / empty → interactive prompts
      └─ no / q      → exit(1)
  → summary + confirm [Y/n]
      ├─ yes → build/execute
      └─ no  → exit(1)

Case 4: 非 TTY 中缺少必填参数
sprout new issue
  → detect missing required inputs: [name]
  → non-TTY => print actionable error
  → exit(1)

Case 5: 用户在交互中取消
interactive prompt
  → user inputs q / quit / exit OR Ctrl+C
  → print "Cancelled. No files were created."
  → exit(1)
```

## Prompt Contract

```python
@dataclass(slots=True)
class PromptRequest:
    name: str
    label: str           # e.g. "name (required)"
    description: str     # one-line field description
    hint: str            # e.g. "string" / "choices: bug, feat"
    default_text: str    # rendered default or ""
```

```text
Prompt rendering format
- <label>
  <description>
  <hint><default>
  >

Examples:
- name (required)
  Issue slug used in generated file names
  text
  >

- type (optional)
  Issue category
  choices: bug, feat, refactor [default: bug]
  >
```

## Input Collection API

```python
def parse_json_input(raw: str) -> dict[str, Any]: ...


def load_json_input_file(path: Path) -> dict[str, Any]: ...


def merge_input_sources(
    base: dict[str, Any],
    overrides: dict[str, str],
) -> dict[str, Any]: ...


def collect_inputs(
    command: CommandSpec,
    provided: dict[str, Any],
    *,
    interactive: bool,
    prompt: Callable[[str], str] = input,
) -> dict[str, Any]: ...


def find_missing_required_inputs(
    command: CommandSpec,
    provided: dict[str, Any],
) -> list[InputSpec]: ...
```

Notes:
- `parse_json_input()` / `load_json_input_file()` 只接受顶层 JSON object
- JSON value 必须能映射到现有 schema：`string | number | enum`
- `collect_inputs(..., interactive=False)` 保持现有职责：严格校验并在缺参时报错
- CLI 层先调用 `find_missing_required_inputs()` 决定是否要引导进入交互模式
- 这样可以把“是否进入交互”保留在 CLI 层，不污染核心校验逻辑

## Cancellation and TTY Rules

| Location | Condition / Input | Behavior |
|----------|-------------------|----------|
| 自动引导交互前 | `stdin` / `stdout` 非 TTY | 不询问，直接失败并给出 `-i` / `--json` / `--json-file` 提示 |
| 显式 `-i` | 当前非 TTY | 立即报错：interactive mode requires a TTY |
| 任意模式 | `--no-input` | 禁止任何交互；缺参时直接失败 |
| 进入交互确认 | `n` / `no` | 不进入交互，退出 |
| 进入交互确认 | `q` / `quit` / `exit` | 视为取消，退出 |
| 字段输入 prompt | `q` / `quit` / `exit` | 立即取消整个命令 |
| 字段输入 prompt | `Ctrl+C` / `EOF` | 转为统一的取消消息 |
| 最终确认 | `n` / `no` | 放弃执行，不写文件 |

## Execution Summary

```text
Interactive summary
Command: issue
Inputs:
  - name = my-task
  - type = bug
Conflict policy: fail
Planned outputs:
  - CREATE issues
  - CREATE issues/26-04-11_my-task.md
Proceed? [Y/n]
```

约束：
- 摘要仅在交互模式下显示
- 摘要基于真实 generation plan，而不是猜测路径
- dry-run 语义保持现状；若用户同时使用交互与 dry-run，摘要后执行 dry-run

## JSON Input Contract

```text
Accepted
--json '{"name":"abc","type":"bug","priority":3}'
--json-file ./inputs.json

Rejected
--json '[1,2,3]'                  # top-level array
--json '{"meta":{"x":1}}'      # nested object
--json '{"tags":["a","b"]}'   # array value
```

Merge order:
```text
json/json-file base
  → apply positional pairs
  → apply --set pairs
  → interactive fill missing values (TTY only)
```

Error style:
- invalid JSON syntax → report parse location if available
- non-object top-level → explicit "JSON input must be an object"
- nested values → explicit "JSON input values must be strings/numbers" style message

## Unknown Command Suggestion

```text
Command not available: isue
Did you mean: issue
Available commands:
  - issue: Create an issue document
  - change: Create a change folder and proposal
Hint: run `sprout list` to inspect all commands
```

实现策略：
- 使用 `difflib.get_close_matches()` 对 `registry.commands.keys()` 做近似匹配
- 输出时优先展示命令描述，避免只给裸名字

## Scope Boundary

不改动：
- `sprout new` 作为主入口的命令结构
- manifest schema
- 非交互快速路径的执行前确认行为
- 生成计划与冲突策略的底层语义
- 动态 `--name value` 风格参数解析
