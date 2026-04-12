---
revision: 1
date: 2026-04-12T15:46:53
trigger: "review-feedback"
---

<!-- @RULE: trigger values: review-feedback | discovery | scope-expansion | correction
本文件记录 design gate 后的范围/设计变更。
spec.md 和 design.md 基线不可变，所有后续演化通过此类文件记录。
文件命名：revisions/NNN-description.md（编号递增）。 -->

# drop toml support

## Reason
用户在 review 中明确要求移除 TOML 支持，认为 YAML 已足够；此前为兼容 Python 3.10 下的 TOML 读取而临时加入 `tomli` 依赖，不符合当前项目希望保持最小依赖面的方向。

## Changes

### Spec Impact
本 change 的实现范围从“保留既有 YAML/TOML/JSON 兼容”收缩为“仅保留 YAML/YML/JSON 兼容”。action/ref/random 设计不变，但相关文档与项目声明不再提及 TOML。

### Design Impact
`sprout/core.py` 的 manifest/config 发现集合移除 `*.toml`；加载逻辑删除 TOML 分支；无需再为 Python 3.10 提供 `tomli` 兜底。

### Task Impact
- 回退 `pyproject.toml` 中新增的 `tomli` 依赖
- 更新 `sprout/core.py`，移除 TOML 发现与读取逻辑
- 调整 `tests/test_core.py`，删除 TOML 兼容断言，改为验证 YAML 优先于 JSON 且 TOML 文件不再被读取
- 更新 `README.md`、`.sspec/project.md` 等文档中的 TOML 描述
