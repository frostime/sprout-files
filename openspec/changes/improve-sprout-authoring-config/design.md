## Context

`sprout` 当前运行时已经支持 `manifest.yaml/yml` 解析，但初始化脚手架、README 示例、测试夹具和本地 `sprout-authoring` Skill 仍然以 JSON 为中心。结果是用户第一次进入 `.sprout/` 时，看见的是缺少注释的 `config.json` / `manifest.json`，而真正可用的数据模型、字段约束和推荐写法散落在 `models.py`、`core.py`、README 和示例代码中。

这次改动同时覆盖三个层面：
- **数据模型表达**：把项目配置和命令包 manifest 的 authoring 模型沉淀成对用户友好的 YAML 结构与字段说明。
- **脚手架体验**：`sprout init` 默认输出带注释的 YAML 文件和示例命令，降低首次填写成本。
- **Agent 协作体验**：本地 `sprout-authoring` Skill 要把“要问什么、字段怎么填、哪些值合法、如何写 assets/template”明确写出来，让 Agent 不必反查实现代码。

约束：
- 不能牺牲现有运行时兼容性，JSON/TOML 仍需可读。
- 现有 `ProjectConfig` / `CommandSpec` / `InputSpec` / `AssetSpec` 数据结构应继续作为内部统一模型。
- YAML 注释只能存在于初始化生成与内置示例中，运行时解析后不依赖注释。

## Goals / Non-Goals

**Goals:**
- 明确 `.sprout` 的内部/外部数据模型映射：`config`、`inputs`、`assets`、模板文件引用与冲突策略。
- 将 `sprout init` 的默认配置与示例命令切换为 YAML，并附带足够的填写提示。
- 重写本地 `sprout-authoring` Skill，使其成为“如何填写 `.sprout`”的权威入口。
- 更新 README、协作文档与测试，使文档、脚手架、运行时三者一致。

**Non-Goals:**
- 不改变 `sprout new` 的执行流程与渲染语义。
- 不引入新的输入类型、模板语法或复杂嵌套 schema。
- 不强制迁移已有 `.json` / `.toml` 项目文件。

## Decisions

### 1) 以现有 dataclass 作为统一数据模型，新增 authoring-facing 字段说明
- **决策**：继续以 `ProjectConfig`、`CommandSpec`、`InputSpec`、`AssetSpec` 作为内部运行时模型；文档和 Skill 明确给出这些模型在 YAML 中的映射字段。
- **原因**：避免出现“文档模型”和“代码模型”两套真相。
- **备选**：新增单独 authoring schema 层。缺点是维护成本高，且当前规模不需要。

### 2) `sprout init` 默认输出 YAML 文件
- **决策**：项目配置改为 `.sprout/config.yaml`；示例命令改为 `.sprout/commands/<name>/manifest.yaml`。
- **原因**：YAML 更适合内置注释、说明默认值和给出多行示例，贴合“教用户怎么填”的目标。
- **备选**：保留 JSON，额外生成 README 注释文档。缺点是填写点和说明分离，体验仍差。

### 3) 配置读取采用多文件回退顺序而不是一次性破坏迁移
- **决策**：项目配置读取改为支持 `config.yaml` / `config.yml` / `config.toml` / `config.json` 的查找顺序；命令 manifest 保持现有多格式支持。
- **原因**：既能让新项目默认走 YAML-first，也不破坏旧项目。
- **备选**：只切换 init 输出，不改读取逻辑。缺点是新生成配置无法直接被运行时发现。

### 4) 本地 Skill 直接包含“填写规则 + 模板示例 + 对齐清单”
- **决策**：将 `sprout-authoring` Skill 拆成几个清晰板块：先对齐需求、数据模型速查、字段填写规则、完整 YAML 示例、修改后验证命令。
- **原因**：让 Agent 在项目内就能获得足够上下文，不必再反查 README 或源码。
- **备选**：只补充一句“参考 README”。缺点是 Agent 首屏仍然不知道怎么填。

### 5) 注释信息以内置静态 YAML 文本模板维护
- **决策**：初始化输出的 YAML 文件采用手写模板字符串，直接包含注释、示例值和解释，而不是把 Python dict dump 成 YAML。
- **原因**：YAML dumper 无法稳定保留高质量注释；手写模板更可控。
- **备选**：使用 YAML 库和 comment-preserving node API。缺点是增加依赖和复杂度。

## Risks / Trade-offs

- **[风险] YAML 解析依赖 PyYAML，部分环境未安装** → **缓解**：保留 JSON/TOML 兼容；README 与错误信息继续明确提示安装 PyYAML 或使用其他格式。
- **[风险] 多格式配置查找顺序可能引发歧义** → **缓解**：定义稳定优先级并在文档中说明，必要时在 doctor 中报告实际命中的文件。
- **[风险] Skill/README/脚手架示例再次漂移** → **缓解**：把数据模型说明集中表达，测试覆盖 init 输出的关键文件名与格式。
- **[风险] 注释模板人工维护成本略升高** → **缓解**：只为少量核心文件（config、example manifests）维护静态模板，收益大于成本。

## Migration Plan

1. 扩展运行时项目配置发现逻辑，先支持 YAML-first 读取。
2. 更新 `sprout init`，生成 `config.yaml` 与 `manifest.yaml` 示例文件。
3. 重写 `sprout-authoring` Skill 与 README / docs，使字段填写说明与默认产物一致。
4. 更新测试夹具，覆盖 YAML 初始化输出与旧格式兼容读取。
5. 保留现有 JSON/TOML 项目不动；新项目默认获得 YAML authoring 体验。

## Open Questions

- 暂不引入自动迁移命令；如果后续用户已有大量 JSON manifest，可在未来考虑 `sprout migrate`。
