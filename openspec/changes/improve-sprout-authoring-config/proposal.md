## Why

当前 `.sprout` 的可填写性较差：用户和 Agent 都需要从代码或零散示例里反推字段含义、可选值和文件结构，导致上手慢、易写错。尤其是 JSON 不便承载注释和填写提示，使内置脚手架与 Skill 无法直接告诉用户“该怎么填”。

## What Changes

- 明确 `.sprout` authoring 数据模型，覆盖项目配置、命令 manifest、输入字段、资产声明及其填写规则。
- 优化内置 `sprout-authoring` Skill，把“先对齐什么、每个字段怎么填、常见写法是什么”讲清楚，并提供可直接套用的示例。
- 将 `sprout init` 生成的项目配置与示例命令 manifest 从 JSON 改为 YAML，内置必要注释、默认值说明和填写提示。
- 让运行时优先支持 YAML 配置，同时保持对已有 JSON/TOML 定义的兼容，降低迁移成本。
- 补充文档与测试，确保 YAML-first 的 authoring 体验、示例输出与运行时解析保持一致。

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `agent-assisted-template-authoring`: 初始化产物与本地 Skill 需要改为 YAML-first，并把 authoring 数据模型与填写指南说明清楚。
- `template-asset-generation`: 运行时需要支持从 YAML 项目配置和 YAML manifest 读取等价定义，并在生成流程中沿用同一数据模型。

## Impact

- 影响 `.sprout` 初始化脚手架、示例命令包、本地 Skill 文案和 README / Agent 协作文档。
- 影响项目配置与命令 manifest 的默认文件格式、注释能力与示例结构。
- 影响配置加载与测试夹具，需要验证 YAML、JSON/TOML 兼容与迁移行为。
