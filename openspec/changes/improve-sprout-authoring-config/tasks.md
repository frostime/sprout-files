## 1. Runtime config model and compatibility

- [ ] 1.1 扩展项目配置发现逻辑，支持 `.sprout/config.yaml` / `.yml` / `.toml` / `.json` 的稳定查找顺序
- [ ] 1.2 保持 `ProjectConfig` 内部模型不变，并补充对 YAML 项目配置的校验与错误提示
- [ ] 1.3 为 YAML-first 配置读取与旧 JSON/TOML 兼容场景补充自动化测试

## 2. Init scaffold YAML-first output

- [ ] 2.1 将 `sprout init` 默认生成的项目配置从 `config.json` 改为带注释的 `config.yaml`
- [ ] 2.2 将内置示例命令包的 `manifest.json` 改为带注释的 `manifest.yaml`
- [ ] 2.3 调整内置 profile / scaffold 文案，使输出说明与 YAML-first 默认行为一致
- [ ] 2.4 更新 init 相关测试，验证新文件名、幂等行为和示例命令输出

## 3. Authoring guidance and docs

- [ ] 3.1 重写 `.sprout/skills/sprout-authoring/SKILL.md` 模板，明确数据模型、字段填写规则、对齐清单与完整示例
- [ ] 3.2 更新 `README.md`，把 `.sprout` 结构、配置示例和 manifest 示例改成 YAML 并补充填写说明
- [ ] 3.3 更新 `docs/agent-collaboration.md`，明确 Agent 如何依据 Skill 引导用户填写 `.sprout`

## 4. Verification and polish

- [ ] 4.1 为 YAML 示例、配置加载和命令包 authoring 体验补充回归测试或夹具
- [ ] 4.2 运行测试与必要的 CLI 验证命令，确认 `sprout init` / `sprout list` / `sprout new` 在 YAML-first 场景下正常工作
