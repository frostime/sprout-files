---
change: "improve-cli-interaction"
updated: "2026-04-11T21:06"
---

# Tasks

## Legend
`[ ]` Todo | `[x]` Done

## Tasks

### Feedback Tasks
- [x] 将默认 example 从 `change` 调整为更中性的 `task`，避免与 `.sspec` 概念混淆
- [x] 在 `AGENTS.md` 开头补充简明项目背景，明确区分 sprout 产品与 `.sspec` 开发流程
**Verification**: `sprout init --with-examples` 生成 `issue/task` 示例；`AGENTS.md` 开头可在 5 秒内完成背景辨识

### Phase 1: 输入通道与 CLI 入口调整 ⏳
- [x] 更新 `sprout/cli.py`：为 `new` 命令添加 `--json`、`--json-file`、`--no-input` 参数
- [x] 更新 `sprout/cli.py`：重构 `_run_new` 的输入装配流程，按 design.md 接入 JSON 基础层与 pairs/--set 覆盖层
- [x] 更新 `sprout/core.py`：实现 JSON 字符串 / 文件读取与输入源合并逻辑
- [x] 更新 `sprout/core.py`：为 JSON 输入增加对象顶层与标量值校验
**Verification**: `uv run pytest tests -k "json or core" -v`；手动验证 `sprout new issue --json ...` 与 `--json-file ...` 都能成功执行

### Phase 2: TTY 感知交互与取消语义 ⏳
- [x] 更新 `sprout/cli.py`：仅在 TTY 且未指定 `--no-input` 时，对缺参场景提供交互引导
- [x] 更新 `sprout/cli.py`：显式 `-i` 但非 TTY 时返回明确错误
- [x] 更新 `sprout/core.py` 或 `sprout/models.py`：补充交互取消、缺失字段检测、必填字符串空值处理
- [x] 更新 `sprout/cli.py`：统一处理 `q/quit/exit/Ctrl+C` 的取消输出
**Verification**: 手动验证 TTY 与非 TTY 分支；`printf '' | uv run sprout new issue -i` 返回 non-TTY 错误；交互中取消时不写文件

### Phase 3: Prompt、错误提示与执行前确认 ⏳
- [x] 更新 `sprout/core.py`：增强 prompt 展示内容（description / choices / default / required）
- [x] 更新 `sprout/cli.py`：缺参错误中输出缺失字段摘要、示例、下一步建议
- [x] 更新 `sprout/cli.py`：未知命令时增加近似匹配建议与描述
- [x] 更新 `sprout/cli.py`：仅在交互模式下输出 generation summary 并请求最终确认
**Verification**: 手动检查 `sprout new issue`、`sprout new isue`、`sprout new issue -i` 的输出；确认 summary 基于真实 generation plan

### Phase 4: 测试与文档 ⏳
- [x] 新增或更新 `tests/`：覆盖 JSON 输入、输入覆盖优先级、非 TTY 保护、交互取消、必填校验、最终确认
- [x] 更新 `README.md`：补充 `sprout new` 的交互行为、TTY 边界、`--json` / `--json-file` 推荐用法
- [x] 在 `temp/<runtime-test-dir>` 下手动验证完整工作流，记录关键命令与结果
**Verification**: `uv run pytest -v` 全量通过；`temp/` 手动验证成功；README 示例与实际行为一致

---

## Progress

**Overall**: 100%

| Phase | Progress | Status |
|-------|----------|--------|
| Feedback Tasks | 2/2 | ✅ |
| Phase 1: 输入通道与 CLI 入口调整 | 4/4 | ✅ |
| Phase 2: TTY 感知交互与取消语义 | 4/4 | ✅ |
| Phase 3: Prompt、错误提示与执行前确认 | 4/4 | ✅ |
| Phase 4: 测试与文档 | 3/3 | ✅ |

**Recent**:
- [2026-04-11T21:06] Plan 阶段完成，拆分为 4 个阶段 15 个任务
- [2026-04-11T21:22] 实现完成并通过定向测试与 temp 目录手动验证
- [2026-04-11T21:31] Review 反馈已收口：默认 example 改为 task，并补充 AGENTS.md 开头背景
