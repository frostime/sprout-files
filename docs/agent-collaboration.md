# sprout Agent 协作指南

## 推荐流程

1. `sprout init` 初始化项目模板工作区
2. 让 Agent 读取 `.sprout/skills/sprout-authoring/SKILL.md`
3. 先对齐需求（命令目的 / 输入字段 / 输出资产 / 冲突策略）
4. 再让 Agent 生成或修改 `.sprout/commands/<name>/` 命令包
5. 用 `sprout doctor` 和 `sprout new <name>` 验证

## 关键约束

- 不要跳过需求对齐直接写模板
- 路径与模板只允许 `{{var}}` 纯插值
- 冲突策略必须显式明确：`fail|overwrite|skip|rename`
- 生成结果应可重复、可审计（建议提交命令包到版本库）

## 常用检查

```bash
sprout list --all
sprout doctor
sprout new issue name=example type=bug
```
