# CLAUDE.md

## 项目概述

`Attractor Before Harness`（ABH）是一个面向 AI 协作开发的收敛框架与 CLI 工具集。核心思想：先把吸引子、基线、计划、验证、审计和记忆显式化，再让开发过程围绕这些对象运行。

## 进入仓库首读

1. `docs/architecture/attractors/abh-core-attractor.md` — active attractor
2. `docs/index.md` — 文档路由入口（含完整 Required Reading Order: project-context、development-roadmap、agent-protocol、quickstart 等 8 份文档）

以上为最小入口；完整必读清单见 `docs/index.md`。

## 关键命令

```bash
abh doctor --json          # 一致性检查
abh plan list              # 列出所有计划
abh next --json            # Agent 默认导航入口
abh report health --json   # 语义压力报告
python3 -m abh.mcp_server  # MCP Server
python3 -m pytest tests/ -v  # 运行测试
```

## Agent 行为约束

- 先读 active attractor，没有 plan 不开工
- verification 不等于完成，close 依赖独立 audit
- 失败假设写 memory
- 写入类操作需显式 `--confirm`
- 不要主动执行 git commit/push 操作，除非用户明确要求
- 注释语言与代码库保持一致（中文）

## 当前项目状态

查询实时状态：

```bash
abh plan list              # 计划列表与状态统计
abh next --json            # 下一步建议动作
abh roadmap check --json   # roadmap queue 状态
abh report health --json   # 语义压力报告
```

当前版本：0.7.0（阶段 7：团队可用与生态集成）
