---
change: "improve-usability"
updated: "2026-04-11T17:39"
---

# Tasks

## Legend
`[ ]` Todo | `[x]` Done

## Tasks

### Phase 1: 模板外部化重构 ⏳

- [ ] 创建模板目录结构 `sprout/templates/`
- [ ] 提取 SKILL 文档到 `sprout/templates/skill-authoring.md`
- [ ] 提取配置模板到 `sprout/templates/config.yaml`
- [ ] 创建 profile 定义 `sprout/templates/profiles/minimal.json`
- [ ] 创建 profile 定义 `sprout/templates/profiles/docs.json`
- [ ] 提取 issue 示例到 `sprout/templates/examples/issue/manifest.yaml`
- [ ] 提取 issue 模板到 `sprout/templates/examples/issue/issue.md`
- [ ] 提取 change 示例到 `sprout/templates/examples/change/manifest.yaml`
- [ ] 提取 change 模板到 `sprout/templates/examples/change/proposal.md`
- [ ] 重构 `sprout/scaffold.py` 从模板目录读取内容
- [ ] 配置 `pyproject.toml` 打包包含 templates 目录
- [ ] 更新 `tests/test_init.py` 适配模板外部化

**Verification**:
- `uv run sprout init --with-examples` 在新目录成功执行
- 生成的 `.sprout/skills/sprout-authoring/SKILL.md` 内容正确
- 生成的示例命令包可以正常使用
- 单元测试通过：`uv run pytest tests/test_init.py -v`

### Phase 2: 依赖管理透明化 ⏳

- [ ] 添加可选依赖到 `pyproject.toml`
- [ ] 改进 YAML 加载错误提示 `sprout/core.py`
- [ ] 更新 README.md 快速开始章节说明可选依赖

**Verification**:
- 在没有 PyYAML 的环境中运行 `sprout list`，错误信息包含安装命令
- README.md 中有清晰的可选依赖说明
- `uv add --optional yaml` 可以正确安装 PyYAML

### Phase 3: Dry-run 模式 ⏳

- [ ] 添加 `--dry-run` 参数到 CLI `sprout/cli.py`
- [ ] 修改 `apply_generation_plan` 支持 dry_run 参数 `sprout/core.py`
- [ ] 调整 CLI 输出格式，dry-run 时添加前缀 `sprout/cli.py`
- [ ] 创建测试文件 `tests/test_dry_run.py`
- [ ] 编写 dry-run 模式测试用例

**Verification**:
- `uv run sprout new issue name=test --dry-run` 输出计划但不创建文件
- 输出每行包含 `[DRY-RUN]` 前缀
- 执行后目标目录不存在
- 单元测试通过：`uv run pytest tests/test_dry_run.py -v`

### Phase 4: 模板静态验证 ⏳

- [ ] 添加 `TemplateValidationIssue` 数据类 `sprout/models.py`
- [ ] 实现 `validate_template_variables` 函数 `sprout/core.py`
- [ ] 扩展 `doctor` 命令调用模板验证 `sprout/cli.py`
- [ ] 创建测试文件 `tests/test_template_validation.py`
- [ ] 编写模板验证测试用例

**Verification**:
- 创建包含未定义变量的测试命令包
- `uv run sprout doctor` 报告模板验证错误
- 错误格式：`Template validation: <command>/<template>: undefined variable '{{var}}'`
- 单元测试通过：`uv run pytest tests/test_template_validation.py -v`

### Phase 5: 集成测试与文档 ⏳

- [ ] 运行完整测试套件 `uv run pytest -v`
- [ ] 在 temp/ 目录测试完整工作流
- [ ] 更新 CHANGELOG（如果存在）
- [ ] 验证所有功能正常工作

**Verification**:
- 所有单元测试通过
- 手动测试覆盖所有新功能
- README.md 文档准确反映新功能
- `sprout --help` 输出包含 `--dry-run` 选项

---

## Progress

**Overall**: 0%

| Phase | Progress | Status |
|-------|----------|--------|
| Phase 1: 模板外部化重构 | 0/12 | ⏳ |
| Phase 2: 依赖管理透明化 | 0/3 | ⏳ |
| Phase 3: Dry-run 模式 | 0/5 | ⏳ |
| Phase 4: 模板静态验证 | 0/5 | ⏳ |
| Phase 5: 集成测试与文档 | 0/4 | ⏳ |

**Recent**:
- [2026-04-11T17:39] Plan 阶段完成，共 5 个阶段 29 个任务
