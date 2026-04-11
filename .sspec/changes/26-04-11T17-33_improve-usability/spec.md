---
name: improve-usability
status: DOING
change-type: single
created: 2026-04-11T17:33:25
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

# improve-usability

## Problem Statement

sprout-cli 核心功能完整（评分 7/10），但存在三个影响 Agent 和人类用户体验的关键问题：

1. **执行前无法预览**：缺少 `--dry-run` 模式，Agent 无法在实际写文件前验证生成计划，导致试错成本高
2. **依赖管理不透明**：PyYAML 为隐式依赖，用户遇到 "YAML support requires PyYAML" 错误时需手动排查安装
3. **模板验证滞后**：模板中引用不存在的变量只在运行时报错，`doctor` 命令无法提前发现问题

这些问题在 Agent 协同场景中尤为突出：Agent 需要多次试错才能确认模板正确性，降低了自动化效率。

## Proposed Solution

### Approach

采用**渐进增强**策略，优先解决 P0 级别的核心体验问题，保持向后兼容：

1. **添加 dry-run 模式**：在 `new` 命令中增加 `--dry-run` 标志，输出生成计划但不写文件，让 Agent 和用户能预览结果
2. **改进依赖提示**：将 PyYAML 加入 `pyproject.toml` 的可选依赖，错误信息中提供明确的安装命令
3. **增强 doctor 静态检查**：扩展 `doctor` 命令，静态分析模板文件中的变量引用，提前发现未定义变量

选择这个方案的原因：
- 不改变现有 API 和数据结构，零破坏性
- 每个改进都是独立的，可以分步实现和测试
- 直接解决评估中发现的高频痛点

### Key Change

**Feat A: Dry-run 模式**
- 在 `sprout new` 命令添加 `--dry-run` / `-n` 标志
- 执行完整的生成计划构建（路径渲染、冲突检测），但跳过文件写入
- 输出格式与正常执行一致，但在每行前加 `[DRY-RUN]` 前缀
- 返回码：计划构建成功返回 0，失败返回 1

**Fix B: 依赖管理透明化**
- 在 `pyproject.toml` 添加 `[project.optional-dependencies]` 节，包含 `yaml = ["pyyaml>=6.0"]`
- 修改 YAML 加载失败的错误信息，提供明确的安装命令：`uv add --optional yaml` 或 `pip install pyyaml`
- 在 README.md 的 "快速开始" 章节添加可选依赖说明

**Feat C: 模板静态验证**
- 扩展 `doctor` 命令，对每个命令包执行模板变量检查
- 检查逻辑：提取模板中的 `{{var}}` 引用，验证 `var` 是否在 `inputs[*].name` 或内置变量列表中
- 报告格式：`Template validation: <command>/<template>: undefined variable '{{unknown}}'`
- 内置变量列表：`YYYY`, `YY`, `MM`, `DD`, `hh`, `mm`, `ss`, `date`, `time`, `datetime`, `timestamp`

**Refactor D: 模板内容外部化**
- 将 `scaffold.py` 中硬编码的模板内容（SKILL 文档、示例命令包、配置文件）移至独立的模板文件
- 新增 `sprout/templates/` 目录，包含：
  - `skill-authoring.md` — sprout-authoring SKILL 文档
  - `config.yaml` — 默认项目配置
  - `profiles/` — 内置 profile 定义（minimal/docs）
  - `examples/issue/` — issue 示例命令包
  - `examples/change/` — change 示例命令包
- `scaffold.py` 改为从模板目录读取内容，仅处理路径解析和文件写入逻辑
- 模板文件支持 `{{var}}` 插值，用于动态内容（如版本号、日期等）

### Scope Summary

| File | Change |
|------|--------|
| `sprout/cli.py` | 添加 `--dry-run` 参数到 `new` 子命令 |
| `sprout/core.py` | 修改 `apply_generation_plan` 支持 dry-run 模式；添加 `validate_template_variables` 函数 |
| `sprout/models.py` | 添加 `TemplateValidationIssue` 数据类 |
| `sprout/scaffold.py` | 重构：从模板目录读取内容，移除硬编码字符串 |
| `sprout/templates/` | 新增：模板目录，包含 SKILL 文档、配置、示例命令包 |
| `sprout/templates/skill-authoring.md` | 新增：从 `scaffold.py` 中提取的 SKILL 文档 |
| `sprout/templates/config.yaml` | 新增：默认项目配置模板 |
| `sprout/templates/profiles/*.json` | 新增：内置 profile 定义 |
| `sprout/templates/examples/issue/` | 新增：issue 示例命令包（manifest + template） |
| `sprout/templates/examples/change/` | 新增：change 示例命令包（manifest + template） |
| `pyproject.toml` | 添加 `[project.optional-dependencies]` 节；配置模板目录打包 |
| `README.md` | 更新快速开始章节，说明可选依赖 |
| `tests/test_dry_run.py` | 新增：测试 dry-run 模式行为 |
| `tests/test_template_validation.py` | 新增：测试模板变量验证逻辑 |
| `tests/test_scaffold.py` | 修改：适配模板外部化后的逻辑 |

### Design Reference

本次变更为功能增强 + 重构，不涉及架构变更。核心实现细节：

**Dry-run 实现**
- 在 `apply_generation_plan` 中添加 `dry_run: bool` 参数，为 `True` 时跳过 `mkdir` 和 `write_text` 调用
- CLI 输出在每行前加 `[DRY-RUN]` 前缀

**模板验证**
- 使用现有的 `VARIABLE_PATTERN` 正则提取变量名，与 `inputs` 和内置变量集合做差集检查
- 在 `doctor` 命令中调用，报告格式：`Template validation: <command>/<template>: undefined variable '{{var}}'`

**错误信息改进**
- 在 `_load_mapping_file` 的 YAML 异常处理中添加安装提示

**模板外部化重构**
- 模板目录结构：
  ```
  sprout/templates/
    skill-authoring.md
    config.yaml
    profiles/
      minimal.json
      docs.json
    examples/
      issue/
        manifest.yaml
        issue.md
      change/
        manifest.yaml
        proposal.md
  ```
- `scaffold.py` 使用 `importlib.resources` 或 `__file__` 路径解析读取模板
- 模板文件支持 `{{version}}` 等变量插值（可选，当前版本不必须）
- `pyproject.toml` 中配置 `[tool.hatch.build.targets.wheel]` 包含 `sprout/templates/`
