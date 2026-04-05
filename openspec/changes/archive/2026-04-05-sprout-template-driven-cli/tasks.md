## 1. CLI foundation & schema

- [x] 1.1 建立 `sprout` CLI 基础命令结构（至少包含 `new`、`init`、`list/doctor` 入口）
- [x] 1.2 定义并实现命令包 manifest 的 v0.1 解析模型（输入类型、资产声明、模板文件引用）
- [x] 1.3 在 schema 中加入 `number` 的可选 `min/max` 约束字段并完成校验映射
- [x] 1.4 在项目配置中加入 `conflict` 策略字段（`fail/overwrite/skip/rename`）
- [x] 1.5 定义 `{{variable}}` 可用变量上下文（用户输入 + 基础时间变量）与命名规范

## 2. Project command discovery

- [x] 2.1 实现从 cwd 向上查找首个 `.sprout/` 的发现算法，并在未命中时给出清晰错误
- [x] 2.2 实现 `.sprout/commands/<command>/` 命令包加载器与有效性校验
- [x] 2.3 实现同名命令冲突检测：冲突双方禁用并输出冲突来源路径
- [x] 2.4 实现“局部失效”策略：单个命令包无效不影响其他命令可用性

## 3. Template asset generation flow

- [x] 3.1 实现 `sprout new <command>` 执行管线（加载定义 → 收集输入 → 校验 → 渲染 → 生成）
- [x] 3.2 实现输入模式：默认非交互参数输入；`-i/--interactive` 触发补全式交互输入
- [x] 3.3 实现 `string`/`number`/`enum` 类型校验与错误提示（含 `number` 的 `min/max`）
- [x] 3.4 实现路径与文件内容的 `{{name}}` 纯文本插值（禁用逻辑流）
- [x] 3.5 实现文件/目录资产生成顺序与冲突策略执行（`fail/overwrite/skip/rename`）
- [x] 3.6 实现 `rename` 策略的确定性重命名规则并输出映射结果

## 4. Init & Agent authoring support

- [x] 4.1 实现 `sprout init`：生成 `.sprout/` 与 `.sprout/commands/` 基础结构
- [x] 4.2 实现 `sprout init` 的自定义骨架能力（可选择 profile 或自定义模板骨架）
- [x] 4.3 实现 `sprout init` 可选示范命令包生成功能（如 issue/change）
- [x] 4.4 实现 `sprout init` 幂等行为：重复执行不覆盖用户已有命令包
- [x] 4.5 在项目内生成 `sprout-authoring` Skill 文档（不安装到全局）
- [x] 4.6 在 Skill/Init 输出中加入“先对齐需求再生成模板”的 Agent 协作提示

## 5. Validation, examples, and docs

- [x] 5.1 增加 discovery / conflict policy / rendering / init 的自动化测试与示例夹具
- [x] 5.2 增加 `number min/max`、`rename` 策略、重复 init 的回归测试
- [x] 5.3 编写用户文档：目录规范、发现规则、冲突策略、交互模式与常见错误排查
- [x] 5.4 编写 Agent 协作文档：`sprout init` 推荐流程与 `sprout-authoring` 使用方式
