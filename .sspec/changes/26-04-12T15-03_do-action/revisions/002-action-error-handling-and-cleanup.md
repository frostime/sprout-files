---
revision: 2
date: 2026-04-12T16:03:38
trigger: "review-feedback"
---

<!-- @RULE: trigger values: review-feedback | discovery | scope-expansion | correction
本文件记录 design gate 后的范围/设计变更。
spec.md 和 design.md 基线不可变，所有后续演化通过此类文件记录。
文件命名：revisions/NNN-description.md（编号递增）。 -->

# action error handling and cleanup

## Reason
独立 code-review subagent 指出两类遗留问题：其一，post-action 在可执行文件不存在、`cwd` 非法或 shell 启动失败时会冒出原始 traceback，而不是统一的 `GenerationError`；其二，文档与代码中还残留少量与已完成 revision 001 不一致的 TOML 文案/分支，需要收口。

## Changes

### Spec Impact
不改变 action/ref/random 的外部能力，仅补充“action 启动失败也必须以用户可读错误返回”的错误语义，并清理与 TOML 移除决策不一致的残留实现/文档。

### Design Impact
`execute_actions()` 增加对 `OSError` / subprocess 启动失败场景的异常包装；测试矩阵补充缺失 executable、非法 cwd 以及 ref 与冲突策略结合的 final-path 语义验证。

### Task Impact
- 修复 `sprout/core.py` 中 action 启动失败时的异常边界
- 清理残留 TOML 分支与 README 文案
- 在 `tests/test_actions.py` 中补充 review 提到的缺失测试
