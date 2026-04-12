---
revision: 3
date: 2026-04-12T16:19:41
trigger: "review-feedback"
---

<!-- @RULE: trigger values: review-feedback | discovery | scope-expansion | correction
本文件记录 design gate 后的范围/设计变更。
spec.md 和 design.md 基线不可变，所有后续演化通过此类文件记录。
文件命名：revisions/NNN-description.md（编号递增）。 -->

# final toml cleanup and docs polish

## Reason
baseline→HEAD 的独立 review 认为主流程已稳，但指出两个残余问题：其一，`_load_mapping_file()` 仍保留 `.toml` 分支，与 revision 001 的“移除 TOML 支持”不完全一致；其二，README 命令总览遗漏 `--dry-run`，存在轻微文档漂移。

## Changes

### Spec Impact
不新增能力，仅把“移除 TOML 支持”收口到实现细节，并补齐已存在 dry-run 能力的文档入口。

### Design Impact
`_load_mapping_file()` 删除 TOML 分支，文件格式加载与发现规则保持一致；README synopsis 补充 `[-n|--dry-run]` 参数。

### Task Impact
- 清理 `sprout/core.py` 中残余 TOML 解析分支
- 更新 `README.md` 的命令总览，补充 dry-run 参数
- 回归测试确保收尾后仍保持全绿
