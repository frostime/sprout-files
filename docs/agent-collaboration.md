# sprout Agent 协作指南

## 推荐流程

1. `sprout init` 初始化项目模板工作区
2. 让 Agent 读取 `.sprout/skills/sprout-authoring/SKILL.md`
3. 先对齐需求（命令目的 / 输入字段 / 输出资产 / 冲突策略）
4. 再让 Agent 生成或修改 `.sprout/commands/<name>/` 命令包
5. 用 `sprout doctor` 和 `sprout new <name>` 验证

## Agent 应该如何引导填写 `.sprout`

在修改任何文件前，Agent 应先把下面 4 件事问清楚：

1. **命令目的**：这个命令要生成什么？
2. **输入字段**：每个字段叫什么、是否必填、是什么类型？
3. **输出资产**：要生成哪些目录/文件？路径规则是什么？
4. **冲突策略**：目标已存在时，应该 fail / overwrite / skip / rename？

如果其中任何一项不明确，Agent 应继续提问，而不是直接生成 manifest。

## 推荐让 Agent 参考的文件

- `.sprout/config.yaml`：项目级默认配置
- `.sprout/commands/<name>/manifest.yaml`：命令定义
- `.sprout/skills/sprout-authoring/SKILL.md`：字段说明、示例与 authoring 规则

## 关键约束

- 不要跳过需求对齐直接写模板
- 路径与模板只允许 `{{var}}` 纯插值
- 冲突策略必须显式明确：`fail|overwrite|skip|rename`
- 生成结果应可重复、可审计（建议提交命令包到版本库）
- 优先使用 YAML authoring：更适合注释、示例和填写提示

## 推荐提示词

可以直接对 Agent 说：

> 读取 `.sprout/skills/sprout-authoring/SKILL.md`，先帮我对齐命令目的、inputs、assets 和 conflict policy，再生成 `.sprout/commands/<name>/manifest.yaml` 和模板文件。

## 常用检查

```bash
sprout list --all
sprout doctor
sprout new issue name=example type=bug
```
