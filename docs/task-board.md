# Attractor Before Harness 任务看板

## 当前阶段

阶段 7：团队可用与生态集成（部分完成）；全部 67 个 plan 已关闭；roadmap queue 剩余 4 项待 materialize

Current: all 67 plans closed; 4 roadmap items queued

## 状态说明

- Todo：尚未开始。
- Doing：正在进行。
- Review：等待审查或验收。
- Done：已完成。
- Blocked：已确认暂不推进，需后续新证据或新计划解除阻塞。

## Sprint 1

| ID | 任务 | 状态 | 产出 |
| --- | --- | --- | --- |
| S1-001 | 建立标准目录结构 | Done | `docs/architecture/`, `docs/plans/`, `docs/audits/`, `docs/memory/` |
| S1-002 | 编写 Attractor 模板 | Done | `docs/architecture/templates/attractor-template.md` |
| S1-003 | 编写 Plan 模板 | Done | `docs/plans/templates/plan-template.md` |
| S1-004 | 编写 Audit 模板 | Done | `docs/audits/templates/audit-template.md` |
| S1-005 | 编写 Memory 模板 | Done | `docs/memory/templates/memory-template.md` |
| S1-006 | 定义项目初始吸引子 | Done | `docs/architecture/attractors/abh-core-attractor.md` |
| S1-007 | 创建 Sprint 1 启动计划 | Done | `docs/plans/plan-001-sprint-1-foundation.md` |
| S1-008 | 创建 Sprint 1 审计占位 | Done | `docs/audits/audit-001-sprint-1-foundation.md` |
| S1-009 | 补充初始 memory 索引 | Done | `docs/memory/README.md` |
| S1-010 | 统一 memory taxonomy | Done | `docs/memory/README.md`, `docs/memory/templates/memory-template.md` |
| S1-011 | 补齐 architecture policies 目录 | Done | `docs/architecture/policies/README.md` |

## Sprint 2

| ID | 任务 | 状态 | 产出 |
| --- | --- | --- | --- |
| S2-001 | CLI 技术选型 | Done | Python standard library |
| S2-002 | CLI 项目骨架 | Done | `abh/`, `pyproject.toml` |
| S2-003 | Plan 创建命令 | Done | `abh plan create` |
| S2-004 | Plan 状态流转 | Done | `abh plan transition` |
| S2-005 | 验证结果记录 | Done | `abh verify record` |
| S2-006 | Sprint 2 启动计划 | Done | `docs/plans/plan-002-sprint-2-local-plan-loop.md` |
| S2-007 | Sprint 2 独立审计 | Done | `docs/audits/audit-002-sprint-2-local-plan-loop.md` |

## Sprint 3

| ID | 任务 | 状态 | 产出 |
| --- | --- | --- | --- |
| S3-001 | Audit 请求命令 | Done | `abh audit request` |
| S3-002 | Audit 记录命令 | Done | `abh audit record` |
| S3-003 | Plan 关闭命令 | Done | `abh close` |
| S3-004 | Memory 添加命令 | Done | `abh memory add` |
| S3-005 | Memory 检索命令 | Done | `abh memory search` |
| S3-006 | Sprint 3 启动计划 | Done | `docs/plans/plan-003-sprint-3-audit-memory-close.md` |
| S3-007 | Sprint 3 独立审计 | Done | `docs/audits/audit-003-sprint-3-audit-memory-close.md` |

## Sprint 4

| ID | 任务 | 状态 | 产出 |
| --- | --- | --- | --- |
| S4-001 | 路由规则设计 | Done | `ROUTES` |
| S4-002 | Route 命令 | Done | `abh route` |
| S4-003 | 漂移分类规则 | Done | `DRIFT_RULES` |
| S4-004 | Drift 分析命令 | Done | `abh drift analyze` |
| S4-005 | 漂移转 follow-up | Done | drift report follow-ups |
| S4-006 | Sprint 4 启动计划 | Done | `docs/plans/plan-004-sprint-4-route-drift.md` |
| S4-007 | Sprint 4 独立审计 | Done | `docs/audits/audit-004-sprint-4-route-drift.md` |

## Sprint 5

| ID | 任务 | 状态 | 产出 |
| --- | --- | --- | --- |
| S5-001 | Runtime 要求说明 | Done | `README.md` |
| S5-002 | Editable install 说明 | Done | `README.md` |
| S5-003 | PYTHONPATH 兜底说明 | Done | `README.md` |
| S5-004 | CLI 示例修正 | Done | `README.md` |
| S5-005 | Sprint 5 启动计划 | Done | `docs/plans/plan-005-runtime-docs-install.md` |
| S5-006 | Sprint 5 独立审计 | Done | `docs/audits/audit-005-runtime-docs-install.md` |

## Sprint 6

| ID | 任务 | 状态 | 产出 |
| --- | --- | --- | --- |
| S6-001 | 历史计划迁移到 abh CLI 管理 | Done | `.abh/plans/`, `docs/plans/` |
| S6-002 | 运行时目录初始化补齐 | Done | `abh/storage.py` |
| S6-003 | README 已知问题修正 | Done | `README.md` |
| S6-004 | Dogfooding memory 记录 | Done | `docs/memory/mem-dogfood-001.md` |
| S6-005 | Sprint 6 启动计划 | Done | `docs/plans/plan-006-stabilize.md` |
| S6-006 | Sprint 6 独立审计 | Done | `docs/audits/audit-006-stabilize.md` |

## Sprint 7

| ID | 任务 | 状态 | 产出 |
| --- | --- | --- | --- |
| S7-001 | Plan 列表命令 | Done | `abh plan list` |
| S7-002 | Memory 列表命令 | Done | `abh memory list` |
| S7-003 | Audit 列表命令 | Done | `abh audit list` |
| S7-004 | Route 注入活跃计划与相关记忆 | Done | `abh route` |
| S7-005 | Drift 支持按计划 non-goals 检测 | Done | `abh drift analyze --plan` |
| S7-006 | uv/uvx 零门槛安装说明 | Done | `README.md`, `pyproject.toml` |
| S7-007 | 独立审计流程 memory | Done | `docs/memory/mem-independent-audit.md`, `docs/memory/mem-audit-template.md` |
| S7-008 | Sprint 7 计划与审计 | Done | `docs/plans/plan-007-sprint-7-dogfood.md`, `docs/audits/audit-007-sprint-7-dogfood.md` |
| S7-009 | 零门槛安装计划与审计 | Done | `docs/plans/plan-007-zero-dep-install.md`, `docs/audits/audit-007b-zero-dep-install.md` |

## Sprint 8

| ID | 任务 | 状态 | 产出 |
| --- | --- | --- | --- |
| S8-001 | 创建 Sprint 8 计划 | Done | `docs/plans/plan-008-roadmap-sync-and-doctor.md` |
| S8-002 | 新增 doctor 一致性检查 | Done | `abh doctor` |
| S8-003 | 为 doctor 补测试 | Done | `tests/test_cli.py` |
| S8-004 | 同步 README、roadmap、task-board | Done | `README.md`, `docs/development-roadmap.md`, `docs/task-board.md` |
| S8-005 | 记录验证与独立审计 | Done | `docs/audits/audit-008-roadmap-sync-and-doctor.md` |

## Sprint 9

| ID | 任务 | 状态 | 产出 |
| --- | --- | --- | --- |
| S9-001 | 创建 Sprint 9 路线对齐计划 | Done | `docs/plans/plan-009-roadmap-phase-alignment.md` |
| S9-002 | 将 roadmap 改为历史线 + 长期阶段线 | Done | `docs/development-roadmap.md` |
| S9-003 | 对齐阶段规划 1-6 | Done | `docs/development-roadmap.md`, `docs/阶段规划.md` |
| S9-004 | 记录关闭后文档同步 memory | Done | `docs/memory/mem-post-close-doc-sync-001.md` |
| S9-005 | Sprint 9 独立审计 | Done | `docs/audits/audit-009-roadmap-phase-alignment.md` |

## Sprint 10

| ID | 任务 | 状态 | 产出 |
| --- | --- | --- | --- |
| S10-001 | 创建 Sprint 10 内核治理计划 | Done | `docs/plans/plan-010-core-governance-hardening.md` |
| S10-002 | 清理 plan-200-demo 状态噪音 | Done | `.abh/plans/`, `docs/plans/` |
| S10-003 | 为新对象加入 schema version | Done | `abh/models.py`, `tests/test_cli.py` |
| S10-004 | 增加 CI 基础门禁 | Done | `.github/workflows/ci.yml` |
| S10-005 | 补充版本策略和关闭后文档同步门禁 | Done | `README.md`, `docs/development-roadmap.md` |
| S10-006 | Sprint 10 独立审计 | Done | `docs/audits/audit-010-core-governance-hardening.md` |

## Sprint 11

| ID | 任务 | 状态 | 产出 |
| --- | --- | --- | --- |
| S11-001 | 创建阶段 1 收尾计划 | Done | `docs/plans/plan-011-stage-1-finalization.md` |
| S11-002 | doctor 检查 schema_version | Done | `abh/core.py`, `tests/test_cli.py` |
| S11-003 | 迁移历史 .abh JSON schema_version | Done | `.abh/` |
| S11-004 | CI 增加 editable install 路径 | Done | `.github/workflows/ci.yml` |
| S11-005 | roadmap 标记阶段 1 完成并顺延 verify-runner | Done | `docs/development-roadmap.md` |
| S11-006 | Sprint 11 独立审计 | Done | `docs/audits/audit-011-stage-1-finalization.md` |

## Sprint 12

| ID | 任务 | 状态 | 产出 |
| --- | --- | --- | --- |
| S12-001 | 创建 Agent Protocol Foundation 计划 | Done | `docs/plans/plan-012-agent-protocol-foundation.md` |
| S12-002 | 将阶段 2 插入为 Agent Protocol 基础 | Done | `docs/阶段规划.md`, `docs/development-roadmap.md` |
| S12-003 | 定义 Agent Protocol 基线 | Done | `docs/architecture/agent-protocol.md` |
| S12-004 | 同步 task-board 当前阶段 | Done | `docs/task-board.md` |
| S12-005 | plan-012 验证与独立审计 | Done | `docs/audits/audit-012-agent-protocol-foundation.md` |
| S12-006 | 启动 JSON 输出与结构化错误计划 | Done | `docs/plans/plan-013-json-output-and-errors.md` |
| S12-007 | 为核心读命令实现 `--json` 输出 | Done | `abh/cli.py`, `tests/test_cli.py` |
| S12-008 | 补充 JSON 输出使用说明 | Done | `README.md` |
| S12-009 | plan-013 验证与独立审计 | Done | `docs/audits/audit-013-json-output-and-errors.md` |
| S12-010 | 启动只读 MCP Server 计划 | Done | `docs/plans/plan-014-readonly-mcp-server.md` |
| S12-011 | 实现只读 MCP stdio Server | Done | `abh/mcp_server.py` |
| S12-012 | 补充 MCP contract 测试 | Done | `tests/test_cli.py` |
| S12-013 | 同步 MCP 使用说明和路线文档 | Done | `README.md`, `docs/architecture/agent-protocol.md`, `docs/development-roadmap.md` |
| S12-014 | plan-014 验证与独立审计 | Done | `docs/audits/audit-014-readonly-mcp-server.md` |
| S12-015 | 启动受控 MCP 写工具计划 | Done | `docs/plans/plan-015-controlled-mcp-write-tools.md` |
| S12-016 | 实现受控 MCP 写工具 | Done | `abh/mcp_server.py` |
| S12-017 | 补充 MCP 写工具 contract 测试 | Done | `tests/test_cli.py` |
| S12-018 | 同步阶段 2 收尾文档 | Done | `README.md`, `docs/architecture/agent-protocol.md`, `docs/development-roadmap.md`, `docs/task-board.md`, `docs/阶段规划.md` |
| S12-019 | plan-015 验证与独立审计 | Done | `docs/audits/audit-015-controlled-mcp-write-tools.md` |

## Sprint 13

| ID | 任务 | 状态 | 产出 |
| --- | --- | --- | --- |
| S13-001 | 启动 Verify Runner MVP 计划 | Done | `docs/plans/plan-016-verify-runner.md` |
| S13-002 | 实现 `abh verify run <plan_id>` | Done | `abh/core.py`, `abh/cli.py` |
| S13-003 | 补充 verify runner TDD 覆盖 | Done | `tests/test_cli.py` |
| S13-004 | 支持 `verify run --json` 输出 | Done | `abh/cli.py`, `tests/test_cli.py` |
| S13-005 | 记录 runner 递归 dogfood memory | Done | `docs/memory/mem-verify-runner-recursion-001.md` |
| S13-006 | 同步阶段 3 启动文档 | Done | `README.md`, `docs/development-roadmap.md`, `docs/task-board.md` |
| S13-007 | plan-016 验证与独立审计 | Done | `docs/audits/audit-016-verify-runner.md` |
| S13-008 | 启动 Plan Update MVP 计划 | Done | `docs/plans/plan-017-plan-update.md` |
| S13-009 | 实现 `abh plan update <plan_id>` | Done | `abh/core.py`, `abh/cli.py` |
| S13-010 | 补充 plan update TDD 覆盖 | Done | `tests/test_cli.py` |
| S13-011 | Dogfood `plan update` 更新 plan-017 自身 | Done | `docs/plans/plan-017-plan-update.md` |
| S13-012 | plan-017 验证与独立审计 | Done | `docs/audits/audit-017-plan-update.md` |

## Sprint 14

| ID | 任务 | 状态 | 产出 |
| --- | --- | --- | --- |
| S14-001 | 启动 Core Module Split 计划 | Done | `docs/plans/plan-018-core-module-split.md` |
| S14-002 | 拆出 plan/audit/verification 领域模块 | Done | `abh/plans.py`, `abh/audits.py`, `abh/verifications.py`, `abh/errors.py`, `abh/core.py` |
| S14-003 | 补充 core 兼容 re-export 边界测试 | Done | `tests/test_cli.py` |
| S14-004 | plan-018 验证与独立审计 | Done | `docs/audits/audit-018-core-module-split.md` |

## Sprint 15

| ID | 任务 | 状态 | 产出 |
| --- | --- | --- | --- |
| S15-001 | 启动 Verification Environment Metadata 计划 | Done | `docs/plans/plan-019-verification-environment-metadata.md` |
| S15-002 | 为 `verify run` 记录结构化环境元数据 | Done | `abh/models.py`, `abh/verifications.py` |
| S15-003 | 补充环境元数据兼容性和路径覆盖测试 | Done | `tests/test_cli.py` |
| S15-004 | 记录 ABH 并行写入 dogfood memory | Done | `docs/memory/mem-abh-write-concurrency-001.md` |
| S15-005 | plan-019 验证与独立审计 | Done | `docs/audits/audit-019-verification-environment-metadata.md` |

## Sprint 16

| ID | 任务 | 状态 | 产出 |
| --- | --- | --- | --- |
| S16-001 | 启动 Stage 3 Functional Plan | Done | `docs/plans/plan-020-stage-3-functional-plan.md` |
| S16-002 | 将阶段 3 剩余功能拆成 plan 队列 | Done | `docs/development-roadmap.md`, `docs/阶段规划.md` |
| S16-003 | 同步 README 和 task-board 当前阶段 | Done | `README.md`, `docs/task-board.md` |
| S16-004 | 校正后续阶段建议 plan 编号 | Done | `docs/development-roadmap.md` |
| S16-005 | plan-020 验证与独立审计 | Done | `docs/audits/audit-020-stage-3-functional-plan.md` |

## Sprint 17

| ID | 任务 | 状态 | 产出 |
| --- | --- | --- | --- |
| S17-001 | 启动 Verification Trust and Stale Detection 计划 | Done | `docs/plans/plan-021-verification-trust-and-stale-detection.md` |
| S17-002 | 为 verification 记录补充 `trust_level` | Done | `abh/models.py`, `abh/verifications.py` |
| S17-003 | 在 `plan status --json` 暴露 latest verification freshness 摘要 | Done | `abh/plans.py`, `abh/cli.py` |
| S17-004 | 补充 trust/stale 回归测试 | Done | `tests/test_cli.py` |
| S17-005 | 同步阶段 3 文档 | Done | `README.md`, `docs/development-roadmap.md`, `docs/阶段规划.md` |
| S17-006 | plan-021 验证与独立审计 | Done | `.abh/verifications/ver-4b7d7719a801.json`, `docs/audits/audit-021-verification-trust-and-stale-detection.md` |

## Sprint 18

| ID | 任务 | 状态 | 产出 |
| --- | --- | --- | --- |
| S18-001 | 启动 Verification Failure Classification 计划 | Done | `docs/plans/plan-022-verification-failure-classification.md` |
| S18-002 | 为 verification 记录补充 `failure_classifications` | Done | `abh/models.py`, `abh/verifications.py` |
| S18-003 | 覆盖 validation failure、timeout、recursive guard 和 environment failure | Done | `tests/test_cli.py` |
| S18-004 | 同步阶段 3 文档 | Done | `README.md`, `docs/development-roadmap.md`, `docs/阶段规划.md` |
| S18-005 | plan-022 验证与独立审计 | Done | `.abh/verifications/ver-0b0b5694cf4f.json`, `docs/audits/audit-022-verification-failure-classification.md` |

## Sprint 19

| ID | 任务 | 状态 | 产出 |
| --- | --- | --- | --- |
| S19-001 | 启动 Atomic ABH Writes 计划 | Done | `docs/plans/plan-023-atomic-abh-writes.md` |
| S19-002 | 为 ABH 存储层补充原子写与本地文件锁 | Done | `abh/storage.py` |
| S19-003 | 统一 plan/audit/memory/drift Markdown 保存路径 | Done | `abh/plans.py`, `abh/audits.py`, `abh/core.py` |
| S19-004 | 补充原子写与并发写入回归测试 | Done | `tests/test_cli.py` |
| S19-005 | 同步阶段 3 文档 | Done | `README.md`, `docs/development-roadmap.md`, `docs/阶段规划.md` |
| S19-006 | plan-023 验证与独立审计 | Done | `.abh/verifications/ver-889f8cddf60c.json`, `docs/audits/audit-023-atomic-abh-writes.md` |

## Sprint 20

| ID | 任务 | 状态 | 产出 |
| --- | --- | --- | --- |
| S20-001 | 启动 Memory/Drift/Routing Module Split 计划 | Done | `docs/plans/plan-024-memory-drift-routing-module-split.md` |
| S20-002 | 拆出 memory 领域模块 | Done | `abh/memory.py`, `abh/core.py` |
| S20-003 | 拆出 drift 领域模块 | Done | `abh/drift.py`, `abh/core.py` |
| S20-004 | 拆出 routing 领域模块 | Done | `abh/routing.py`, `abh/core.py` |
| S20-005 | 补充 core re-export 和 CLI/MCP 回归测试 | Done | `tests/test_cli.py` |
| S20-006 | 同步阶段 3 文档 | Done | `README.md`, `docs/development-roadmap.md`, `docs/阶段规划.md` |
| S20-007 | plan-024 验证与独立审计 | Done | `.abh/verifications/ver-e44f2ac2dc7a.json`, `docs/audits/audit-024-memory-drift-routing-module-split.md` |

## Sprint 21

| ID | 任务 | 状态 | 产出 |
| --- | --- | --- | --- |
| S21-001 | 启动 Stage 3 Finalization 计划 | Done | `docs/plans/plan-025-stage-3-finalization.md` |
| S21-002 | 判断 v0.3 Verify Runner 里程碑 readiness | Done | `docs/development-roadmap.md`, `docs/阶段规划.md` |
| S21-003 | 同步 README 和 roadmap 到阶段 3 收尾状态 | Done | `README.md`, `docs/development-roadmap.md` |
| S21-004 | 明确阶段 4 Attractor Registry 启动条件 | Done | `docs/development-roadmap.md`, `docs/阶段规划.md` |
| S21-005 | plan-025 验证与独立审计 | Done | `.abh/verifications/ver-3a94943557a8.json`, `docs/audits/audit-025-stage-3-finalization.md` |

## Sprint 22

目标：完成 v0.3.0 正式发布准备，不引入阶段 4 功能。

| ID | 任务 | 状态 | 产出 |
| --- | --- | --- | --- |
| S22-001 | 启动 v0.3 Release Prep 计划 | Done | `docs/plans/plan-026-v0-3-release-prep.md` |
| S22-002 | 提升版本元数据到 0.3.0 | Done | `pyproject.toml`, `abh/__init__.py` |
| S22-003 | 编写 v0.3.0 release notes | Done | `docs/releases/v0.3.0.md` |
| S22-004 | 同步 README、roadmap、阶段规划和后续计划编号 | Done | `README.md`, `docs/development-roadmap.md`, `docs/阶段规划.md` |
| S22-005 | release-prep 验证、审计、关闭和 tag | Done | `audit-026-v0-3-release-prep`, `v0.3.0` |

## Sprint 23

目标：启动阶段 4 Agent-First 吸引子入口层，先把 Agent-First Command Contract 写成技术底座，再进入 attractor/init/setup/hooks/next 等实现计划。

| ID | 任务 | 状态 | 产出 |
| --- | --- | --- | --- |
| S23-001 | 启动 Stage 4 Attractor Entry 计划 | Done | `docs/plans/plan-027-stage-4-attractor-entry-plan.md` |
| S23-002 | 将 Agent-First Command Contract 纳入 Agent Protocol | Done | `docs/architecture/agent-protocol.md` |
| S23-003 | 同步 README、roadmap、阶段规划和 task-board | Done | `README.md`, `docs/development-roadmap.md`, `docs/阶段规划.md`, `docs/task-board.md` |
| S23-004 | 确认阶段 4 计划队列和下一条实现计划 | Done | `plan-028-agent-first-command-contract` |
| S23-005 | plan-027 验证与独立审计 | Done | `.abh/verifications/ver-49c8fc69492a.json`, `docs/audits/audit-027-stage-4-attractor-entry-plan.md` |

## Sprint 24

目标：实现 Stage 4 的 Agent-First Command Contract 技术底座，让 CLI、MCP、后续 hooks/setup/next 共用命令元数据、JSON envelope、side effects 和确认边界。

| ID | 任务 | 状态 | 产出 |
| --- | --- | --- | --- |
| S24-001 | 启动 Agent-First Command Contract 计划 | Done | `docs/plans/plan-028-agent-first-command-contract.md` |
| S24-002 | 抽出共享 command contract 模块 | Done | `abh/commands.py` |
| S24-003 | 让 CLI JSON envelope 使用共享契约 helper | Done | `abh/cli.py`, `abh/commands.py` |
| S24-004 | 让 MCP tool definitions 使用共享契约 metadata | Done | `abh/mcp_server.py`, `abh/commands.py` |
| S24-005 | 对齐 MCP `abh_plan_status` 与 CLI `plan status --json` 的 `verification_summary` | Done | `abh/mcp_server.py`, `tests/test_cli.py` |
| S24-006 | 同步 Agent Protocol、README、roadmap 和阶段规划 | Done | `docs/architecture/agent-protocol.md`, `README.md`, `docs/development-roadmap.md`, `docs/阶段规划.md` |
| S24-007 | plan-028 验证与独立审计 | Done | `.abh/verifications/ver-400d1483ff53.json`, `docs/audits/audit-028-agent-first-command-contract.md` |

## Sprint 25

目标：把 active attractor 从 Markdown 约定升级为 Agent 可读、CLI 可管理、MCP 可读取的一等 ABH 对象，并让 ready plan 绑定当前 active attractor。

| ID | 任务 | 状态 | 产出 |
| --- | --- | --- | --- |
| S25-001 | 启动 Attractor Registry MVP 计划 | Done | `docs/plans/plan-029-attractor-registry.md` |
| S25-002 | 新增 AttractorRecord、存储路径和领域模块 | Done | `abh/models.py`, `abh/storage.py`, `abh/attractors.py` |
| S25-003 | 新增 `abh attractor` CLI 命令 | Done | `abh/cli.py`, `tests/test_cli.py` |
| S25-004 | 接入 Agent-First command contract 和 MCP 只读工具 | Done | `abh/commands.py`, `abh/mcp_server.py` |
| S25-005 | ready plan 校验 active attractor | Done | `abh/plans.py`, `tests/test_cli.py` |
| S25-006 | 注册当前仓库 active attractor | Done | `.abh/attractors/attractor-abh-core.json`, `docs/architecture/attractors/abh-core-attractor.md` |
| S25-007 | 同步 Stage 4 文档 | Done | `README.md`, `docs/development-roadmap.md`, `docs/阶段规划.md`, `docs/architecture/agent-protocol.md` |
| S25-008 | plan-029 验证与独立审计 | Done | `.abh/verifications/ver-ed85ce8d3ae8.json`, `docs/audits/audit-029-attractor-registry.md` |

## Sprint 26

目标：建立 roadmap queue 与 plan 编号 materialize 机制，避免临时插入治理计划时批量改写未来 plan 编号。

| ID | 任务 | 状态 | 产出 |
| --- | --- | --- | --- |
| S26-001 | 启动 Roadmap Queue and Plan Numbering 计划 | Done | `docs/plans/plan-030-roadmap-queue-and-plan-numbering.md` |
| S26-002 | 新增 roadmap queue 数据文件和领域模块 | Done | `.abh/roadmap.json`, `abh/roadmap.py` |
| S26-003 | 新增 `abh roadmap list/next-id/check/materialize` | Done | `abh/cli.py`, `abh/commands.py`, `abh/mcp_server.py` |
| S26-004 | 接入 doctor 编号/queue 一致性检查 | Done | `abh/core.py`, `tests/test_cli.py` |
| S26-005 | 将未来计划文档改为稳定 queue key | Done | `README.md`, `docs/development-roadmap.md`, `docs/阶段规划.md`, `docs/architecture/agent-protocol.md` |
| S26-006 | plan-030 验证与独立审计 | Done | `.abh/verifications/`, `docs/audits/audit-030-roadmap-queue-and-plan-numbering.md` |

## Sprint 27

目标：吸收 AGE 模板的 truth precedence 和 owner-doc 分层，把它们固化为 `abh init`、Agent setup、`abh next` 和 onboarding check 的前置文档基线。

| ID | 任务 | 状态 | 产出 |
| --- | --- | --- | --- |
| S27-001 | 启动 Truth Precedence and AGE Docs Baseline 计划 | Done | `docs/plans/plan-031-truth-precedence-and-age-docs.md` |
| S27-002 | 新增顶级文档路由 | Done | `docs/index.md` |
| S27-003 | 新增 context owner docs | Done | `docs/context/source-of-truth.md`, `docs/context/project-context.md`, `docs/context/conventions.md`, `docs/context/codebase-map.md` |
| S27-004 | 同步 Stage 4 roadmap 和 Agent Protocol | Done | `docs/development-roadmap.md`, `docs/architecture/agent-protocol.md` |
| S27-005 | plan-031 验证与独立审计 | Done | `.abh/verifications/ver-a628d91e3765.json`, `docs/audits/audit-031-truth-precedence-and-age-docs.md` |

## Sprint 28

目标：实现 `abh init` 的最小 Agent-First 初始化切片，让新仓库围绕 active attractor 建立 `.abh/`、docs baseline 和 AGE owner docs，并且写入前可机器读取 preview。

| ID | 任务 | 状态 | 产出 |
| --- | --- | --- | --- |
| S28-001 | materialize ABH Init Active Attractor 计划 | Done | `stage4.abh-init-active-attractor` -> `docs/plans/plan-032-abh-init-active-attractor.md` |
| S28-002 | 定义 `abh init` command contract 和 CLI JSON preview | Done | `abh/commands.py`, `abh/cli.py`, `tests/test_cli.py` |
| S28-003 | 实现初始化写入与不覆盖保护 | Done | `abh/init.py`, `tests/test_cli.py` |
| S28-004 | 同步 README、roadmap、阶段规划和 Agent Protocol | Done | `README.md`, `docs/development-roadmap.md`, `docs/阶段规划.md`, `docs/architecture/agent-protocol.md` |
| S28-005 | plan-032 验证、独立审计和关闭 | Done | `.abh/verifications/ver-1e9ba9045ad4.json`, `docs/audits/audit-032-abh-init-active-attractor.md` |

## Sprint 29

目标：把 `stage4.agent-contract-setup` dogfood 成 `plan-033-agent-contract-setup`，导出 Codex、Claude Code 和通用 MCP 客户端可读取的只读 setup bundle，并明确当前切片不写 agent 配置文件。

| ID | 任务 | 状态 | 产出 |
| --- | --- | --- | --- |
| S29-001 | materialize Agent Contract Setup 计划 | Done | `stage4.agent-contract-setup` -> `docs/plans/plan-033-agent-contract-setup.md` |
| S29-002 | 定义 agent setup command contract 和红灯测试 | Done | `abh/commands.py`, `tests/test_cli.py` |
| S29-003 | 实现 `abh agent setup {codex,claude-code,mcp} --json` | Done | `abh/agent_setup.py`, `abh/cli.py`, `tests/test_cli.py` |
| S29-004 | 同步 README、roadmap、task-board、Agent Protocol 和 codebase map | Done | `README.md`, `docs/development-roadmap.md`, `docs/task-board.md`, `docs/architecture/agent-protocol.md`, `docs/context/codebase-map.md` |
| S29-005 | plan-033 验证、独立审计和关闭 | Done | `docs/audits/audit-033-agent-contract-setup.md`, `docs/plans/plan-033-agent-contract-setup.md` |

## Sprint 30

目标：把 `stage4.git-hooks-guardrails` dogfood 成 `plan-034-git-hooks-guardrails`，交付本地 default pre-commit guardrail MVP：可预览、必须确认写入、只管理 ABH 标记 hook，并保护 doctor、roadmap queue 和 diff whitespace 基础不变量。

| ID | 任务 | 状态 | 产出 |
| --- | --- | --- | --- |
| S30-001 | materialize Git Hooks Guardrails 计划 | Done | `stage4.git-hooks-guardrails` -> `docs/plans/plan-034-git-hooks-guardrails.md` |
| S30-002 | 定义 hooks command contract 和红灯测试 | Done | `abh/commands.py`, `tests/test_cli.py` |
| S30-003 | 实现 `abh hooks profile --json` 和 `abh hooks install` | Done | `abh/hooks.py`, `abh/cli.py`, `tests/test_cli.py` |
| S30-004 | 同步 README、roadmap、task-board、Agent Protocol 和 codebase map | Done | `README.md`, `docs/development-roadmap.md`, `docs/task-board.md`, `docs/architecture/agent-protocol.md`, `docs/context/codebase-map.md` |
| S30-005 | plan-034 验证、独立审计和关闭 | Done | `.abh/verifications/ver-4b6212dd48da.json`, `docs/audits/audit-034-git-hooks-guardrails.md`, `docs/plans/plan-034-git-hooks-guardrails.md` |

## Sprint 31

目标：把 `stage4.abh-next-and-onboarding-check` dogfood 成 `plan-035-abh-next-and-onboarding-check`，交付只读 Agent navigation 和 onboarding readiness MVP，让 Agent 能问“下一步做什么”和“这个仓库是否 ABH-ready”。

| ID | 任务 | 状态 | 产出 |
| --- | --- | --- | --- |
| S31-001 | materialize ABH Next and Onboarding Check 计划 | Done | `stage4.abh-next-and-onboarding-check` -> `docs/plans/plan-035-abh-next-and-onboarding-check.md` |
| S31-002 | 定义 next/onboarding command contract 和红灯测试 | Done | `abh/commands.py`, `tests/test_cli.py` |
| S31-003 | 实现 `abh next --json` 和 `abh onboarding check --json` | Done | `abh/navigation.py`, `abh/cli.py`, `tests/test_cli.py` |
| S31-004 | 同步 README、roadmap、task-board、Agent Protocol 和 codebase map | Done | `README.md`, `docs/development-roadmap.md`, `docs/task-board.md`, `docs/architecture/agent-protocol.md`, `docs/context/codebase-map.md` |
| S31-005 | plan-035 验证、独立审计和关闭 | Done | `docs/audits/audit-035-abh-next-and-onboarding-check.md`, `docs/plans/plan-035-abh-next-and-onboarding-check.md` |

## Sprint 32

目标：把 `stage4.quickstart-recipes-and-distribution` dogfood 成 `plan-036-quickstart-recipes-and-distribution`，补齐 Stage 4 adoption 入口文档、Agent recipes 和当前支持的 git/editable 分发路径，同时不发布 PyPI、不引入 release automation 或团队策略。

| ID | 任务 | 状态 | 产出 |
| --- | --- | --- | --- |
| S32-001 | materialize Quickstart Recipes and Distribution 计划 | Done | `stage4.quickstart-recipes-and-distribution` -> `docs/plans/plan-036-quickstart-recipes-and-distribution.md` |
| S32-002 | 定义 quickstart/recipes/distribution 文档范围 | Done | `docs/plans/plan-036-quickstart-recipes-and-distribution.md`, `.abh/roadmap.json` |
| S32-003 | 新增 quickstart 和 recipes 文档 | Done | `docs/quickstart.md`, `docs/recipes/` |
| S32-004 | 同步 README、docs index、Agent Protocol、roadmap、task-board 和 codebase map | Done | `README.md`, `docs/index.md`, `docs/development-roadmap.md`, `docs/task-board.md`, `docs/architecture/agent-protocol.md`, `docs/context/codebase-map.md` |
| S32-005 | plan-036 验证、opencode DeepSeek 审计和关闭 | Done | `docs/audits/audit-036-quickstart-recipes-and-distribution.md`, `docs/plans/plan-036-quickstart-recipes-and-distribution.md` |

## Sprint 33

目标：把 `stage5.audit-prompt-bundle` dogfood 成 `plan-037-audit-prompt-bundle`，交付只读 `abh audit bundle <plan> --json`，让人类或独立 Agent 可以拿到一致的审计 prompt、证据路径和最新 verification freshness 摘要，同时不自动调用模型、不记录 verdict、不改变关闭门禁。

| ID | 任务 | 状态 | 产出 |
| --- | --- | --- | --- |
| S33-001 | materialize Audit Prompt Bundle 计划 | Done | `stage5.audit-prompt-bundle` -> `docs/plans/plan-037-audit-prompt-bundle.md` |
| S33-002 | 定义 audit bundle command contract 和红灯测试 | Done | `abh/commands.py`, `tests/test_cli.py` |
| S33-003 | 实现 `abh audit bundle <plan> --json` | Done | `abh/audit_bundle.py`, `abh/cli.py`, `tests/test_cli.py` |
| S33-004 | 同步 README、roadmap、task-board、Agent Protocol 和 codebase map | Done | `README.md`, `docs/development-roadmap.md`, `docs/task-board.md`, `docs/architecture/agent-protocol.md`, `docs/context/codebase-map.md` |
| S33-005 | plan-037 验证、opencode DeepSeek 审计和关闭 | Done | `docs/audits/audit-037-audit-prompt-bundle.md`, `docs/plans/plan-037-audit-prompt-bundle.md` |

## Sprint 34

目标：把 `stage5.independent-audit-gate` dogfood 成 `plan-038-independent-audit-gate`，让 audit verdict 显式记录审计来源/上下文、独立性声明和所依据的 verification，并让 `abh close` 只接受绑定当前 fresh passing verification 的 independent pass audit。

| ID | 任务 | 状态 | 产出 |
| --- | --- | --- | --- |
| S34-001 | materialize Independent Audit Gate 计划 | Done | `stage5.independent-audit-gate` -> `docs/plans/plan-038-independent-audit-gate.md` |
| S34-002 | 定义 audit context 和 close gate 红灯测试 | Done | `tests/test_cli.py` |
| S34-003 | 实现 audit metadata 与 independent/fresh close gate | Done | `abh/models.py`, `abh/audits.py`, `abh/plans.py`, `abh/cli.py`, `abh/commands.py`, `abh/mcp_server.py` |
| S34-004 | 同步 README、roadmap、task-board、Agent Protocol 和 codebase map | Done | `README.md`, `docs/development-roadmap.md`, `docs/task-board.md`, `docs/architecture/agent-protocol.md`, `docs/context/codebase-map.md` |
| S34-005 | plan-038 验证、独立审计和关闭 | Done | `.abh/verifications/`, `docs/audits/audit-038-independent-audit-gate.md`, `docs/plans/plan-038-independent-audit-gate.md` |

## Sprint 35

目标：把 `stage6.quality-signal-model` dogfood 成 `plan-039-quality-signal-model`，先定义 product-quality-first / agent-navigation-second 的质量信号词汇，再让 drift、memory、route、`abh next` 和 health report 复用。

| ID | 任务 | 状态 | 产出 |
| --- | --- | --- | --- |
| S35-001 | materialize Quality Signal Model 计划 | Done | `stage6.quality-signal-model` -> `docs/plans/plan-039-quality-signal-model.md` |
| S35-002 | 定义 Stage 6 quality signal model | Done | `docs/architecture/quality-signals.md` |
| S35-003 | 同步 roadmap、task-board、Agent Protocol 和 codebase map | Done | `docs/development-roadmap.md`, `docs/task-board.md`, `docs/architecture/agent-protocol.md`, `docs/context/codebase-map.md` |
| S35-004 | plan-039 验证、独立审计和关闭 | Done | `docs/audits/audit-039-quality-signal-model.md`, `docs/plans/plan-039-quality-signal-model.md` |

## Sprint 36

目标：把 `stage6.drift-quality` dogfood 成 `plan-040-drift-quality`，让 drift finding 从简单规则命中升级为带 severity、confidence、matched span、source excerpt、evidence path 和 recommendation 的质量信号。

| ID | 任务 | 状态 | 产出 |
| --- | --- | --- | --- |
| S36-001 | materialize Drift Quality 计划 | Done | `stage6.drift-quality` -> `docs/plans/plan-040-drift-quality.md` |
| S36-002 | 定义 drift quality 红灯测试 | Done | `tests/test_cli.py` |
| S36-003 | 实现 drift finding 质量信号元数据 | Done | `abh/models.py`, `abh/drift.py`, `abh/cli.py`, `abh/mcp_server.py` |
| S36-004 | 同步 README、roadmap、task-board、quality signals 和 codebase map | Done | `README.md`, `docs/development-roadmap.md`, `docs/task-board.md`, `docs/architecture/quality-signals.md`, `docs/context/codebase-map.md` |
| S36-005 | plan-040 验证、独立审计和关闭 | Done | `docs/audits/audit-040-drift-quality.md`, `docs/plans/plan-040-drift-quality.md` |

## Sprint 37

目标：把 `stage6.memory-index` dogfood 成 `plan-041-memory-index`，让 memory 从 keyword-searchable notes 升级为带 tags、status、typed relationships 和 supersession 的可复用质量知识。

| ID | 任务 | 状态 | 产出 |
| --- | --- | --- | --- |
| S37-001 | materialize Memory Index 计划 | Done | `stage6.memory-index` -> `docs/plans/plan-041-memory-index.md` |
| S37-002 | 定义 memory metadata 红灯测试 | Done | `tests/test_cli.py` |
| S37-003 | 实现 memory metadata、Markdown 渲染和 relationship/status filters | Done | `abh/models.py`, `abh/memory.py`, `abh/cli.py` |
| S37-004 | 接入 Agent-First command contract 和 MCP 写/读工具 | Done | `abh/commands.py`, `abh/mcp_server.py` |
| S37-005 | 同步 README、roadmap、task-board、quality signals、Agent Protocol 和 codebase map | Done | `README.md`, `docs/development-roadmap.md`, `docs/task-board.md`, `docs/architecture/quality-signals.md`, `docs/architecture/agent-protocol.md`, `docs/context/codebase-map.md` |
| S37-006 | plan-041 验证、独立审计和关闭 | Done | `.abh/verifications/`, `docs/audits/audit-041-memory-index.md`, `docs/plans/plan-041-memory-index.md` |

## Sprint 38

目标：把 `stage6.project-health-report` dogfood 成 `plan-042-project-health-report`，让 health report 从普通统计报表升级为 product-quality-first 的语义压力报告，优先暴露 unbound commitment pressure、stale proof、semantic leakage、J-flow-only evidence、orphaned memory 和 repeated leakage。

| ID | 任务 | 状态 | 产出 |
| --- | --- | --- | --- |
| S38-001 | materialize Project Health Report 计划 | Done | `stage6.project-health-report` -> `docs/plans/plan-042-project-health-report.md` |
| S38-002 | 定义 semantic pressure report 详细实施计划 | Done | `docs/superpowers/plans/2026-05-30-project-health-report.md` |
| S38-003 | 定义 report health 红灯测试 | Done | `tests/test_cli.py` |
| S38-004 | 实现 read-only health reporting module | Done | `abh/reporting.py`, `abh/cli.py`, `abh/commands.py`, `abh/mcp_server.py` |
| S38-005 | 同步 README、roadmap、task-board、quality signals、Agent Protocol 和 codebase map | Done | `README.md`, `docs/development-roadmap.md`, `docs/task-board.md`, `docs/architecture/quality-signals.md`, `docs/architecture/agent-protocol.md`, `docs/context/codebase-map.md` |
| S38-006 | plan-042 验证、独立审计和关闭 | Done | `.abh/verifications/`, `docs/audits/audit-042-project-health-report.md`, `docs/plans/plan-042-project-health-report.md` |

## Stage 6 Semantic Commitment Follow-Ups

目标：把 AGE/PHS 文章启发固化为后续 ABH queue，避免 health report 之后遗忘 plan reference、commitment phase、semantic conservation 和 owner-doc stable commitments。

| ID | 任务 | 状态 | 产出 |
| --- | --- | --- | --- |
| S6-F01 | Plan Reference Set | Deferred | `stage6.plan-reference-set` -> `plan-043-plan-reference-set` |
| S6-F02 | Commitment Phase State | Done | `stage6.commitment-phase-state` -> `plan-049-commitment-phase-state` |
| S6-F03 | Audit Semantic Conservation | Done | `stage6.audit-semantic-conservation` -> `plan-050-audit-semantic-conservation` |
| S6-F04 | Owner Doc Stable Commitments | Done | `stage6.owner-doc-stable-commitments` -> `plan-051-owner-doc-stable-commitments` |
| S6-F05 | Post-Close Freshness Semantics | Done | `stage6.post-close-freshness-semantics` -> `plan-052-post-close-freshness-semantics` |
| S6-F06 | Command Contract Runtime Registry | Done | `stage6.command-contract-runtime-registry` -> `plan-044-command-contract-runtime-registry` |
| S6-F07 | Repository Write Transaction Boundary | Done | `stage6.repository-write-transaction-boundary` -> `plan-045-repository-write-transaction-boundary` |
| S6-F08 | Schema Validation and Migration | Done | `stage6.schema-validation-and-migration` -> `plan-046-schema-validation-and-migration` |
| S6-F09 | Verification Runner Trust Policy | Done | `stage6.verification-runner-trust-policy` -> `plan-047-verification-runner-trust-policy` |
| S6-F10 | Test Suite Domain Split | Done | `stage6.test-suite-domain-split` -> `plan-048-test-suite-domain-split` |

| S7-F01 | CI Templates | Done | `stage7.ci-templates` -> `plan-053-ci-templates` |
| S7-F02 | Multi Repo Sharing | Closed（audit rejected） | `stage7.multi-repo-sharing` → `plan-054-multi-repo-sharing`（closed, audit rejected, re-materialize needed） |
| S7-F03 | Team Policy and Release Automation | Todo | `stage7.team-policy-and-release-automation` |
| ADOPT-F01 | ABH Workflow Skill Packaging | Done | `adoption.abh-workflow-skill` -> `plan-055-abh-workflow-skill`（closed） |

## Sprint 39

目标：把 `stage6.plan-reference-set` dogfood 成 `plan-043-plan-reference-set`，让 plan 明确声明本轮工作必须参考的事实星座。

| ID | 任务 | 状态 | 产出 |
| --- | --- | --- | --- |
| S39-001 | materialize Plan Reference Set 计划 | Done | `stage6.plan-reference-set` -> `docs/plans/plan-043-plan-reference-set.md` |
| S39-002 | 定义 Reference Set 详细实施计划 | Done | `docs/superpowers/plans/2026-05-30-plan-reference-set.md` |
| S39-003 | 定义 Reference Set 红灯测试 | Todo | `tests/test_cli.py` |
| S39-004 | 实现 PlanRecord/RoadmapItem Reference Set 模型与渲染 | Todo | `abh/models.py`, `abh/plans.py`, `abh/roadmap.py` |
| S39-005 | 接入 CLI、Agent-First command contract 和 MCP create flow | Todo | `abh/cli.py`, `abh/commands.py`, `abh/mcp_server.py` |
| S39-006 | 同步 README、plan template、quality signals、roadmap、task-board 和 codebase map | Todo | `README.md`, `docs/plans/templates/plan-template.md`, `docs/architecture/quality-signals.md`, `docs/development-roadmap.md`, `docs/task-board.md`, `docs/context/codebase-map.md` |
| S39-007 | plan-043 验证、独立审计和关闭 | Todo | `.abh/verifications/`, `docs/audits/audit-043-plan-reference-set.md`, `docs/plans/plan-043-plan-reference-set.md` |

## Sprint 40

目标：把架构评审中的首个优化点 dogfood 成 `plan-044-command-contract-runtime-registry`，先降低 command contract / CLI / MCP 的协议事实源分裂风险。

| ID | 任务 | 状态 | 产出 |
| --- | --- | --- | --- |
| S40-001 | materialize Command Contract Runtime Registry 计划 | Done | `stage6.command-contract-runtime-registry` -> `docs/plans/plan-044-command-contract-runtime-registry.md` |
| S40-002 | 定义架构硬化详细实施计划 | Done | `docs/superpowers/plans/2026-06-04-command-contract-runtime-registry.md` |
| S40-003 | 同步 architecture hardening queue | Done | `.abh/roadmap.json`, `docs/development-roadmap.md`, `docs/task-board.md` |
| S40-004 | 固定 MCP 使用共享 command-layer error payload 的红灯测试 | Done | `tests/test_cli.py` |
| S40-005 | 下沉 error payload helper 并解除 MCP 对 CLI 协议 helper 的导入 | Done | `abh/commands.py`, `abh/cli.py`, `abh/mcp_server.py` |
| S40-006 | plan-044 验证、独立审计和关闭 | Done | `.abh/verifications/ver-1a1bbf356998.json`, `docs/audits/audit-044-command-contract-runtime-registry.md`, `docs/plans/plan-044-command-contract-runtime-registry.md` |

## Sprint 41

目标：把 `stage6.repository-write-transaction-boundary` dogfood 成 `plan-045-repository-write-transaction-boundary`，统一 ABH JSON/Markdown 双写边界，降低 split-state 风险。

| ID | 任务 | 状态 | 产出 |
| --- | --- | --- | --- |
| S41-001 | materialize Repository Write Transaction Boundary 计划 | Done | `stage6.repository-write-transaction-boundary` -> `docs/plans/plan-045-repository-write-transaction-boundary.md` |
| S41-002 | 定义 repository write transaction boundary 实施计划 | Done | `docs/superpowers/plans/2026-06-04-repository-write-transaction-boundary.md` |
| S41-003 | 调整 `abh next` 让 blocked/deferred plan 不阻塞 queued roadmap | Done | `abh/navigation.py`, `tests/test_cli.py` |
| S41-004 | 定义 JSON/Markdown pair write 红灯测试 | Done | `tests/test_cli.py` |
| S41-005 | 实现 storage pair write boundary 并接入核心 save 路径 | Done | `abh/storage.py`, `abh/plans.py`, `abh/audits.py`, `abh/memory.py`, `abh/drift.py`, `abh/attractors.py` |
| S41-006 | 同步 roadmap、task-board 和 transaction boundary 文档说明 | Done | `docs/development-roadmap.md`, `docs/task-board.md` |
| S41-007 | plan-045 验证、独立审计和关闭 | Done | `.abh/verifications/ver-3f470aa8d592.json`, `docs/audits/audit-045-repository-write-transaction-boundary-r2.md`, `docs/plans/plan-045-repository-write-transaction-boundary.md` |

## Sprint 42

目标：把 `stage6.schema-validation-and-migration` dogfood 成 `plan-046-schema-validation-and-migration`，为 `.abh` record 增加结构校验、版本迁移边界和未知字段策略。

| ID | 任务 | 状态 | 产出 |
| --- | --- | --- | --- |
| S42-001 | materialize Schema Validation and Migration 计划 | Done | `stage6.schema-validation-and-migration` -> `docs/plans/plan-046-schema-validation-and-migration.md` |
| S42-002 | 定义 schema validation/migration 实施计划 | Done | `docs/superpowers/plans/2026-06-05-schema-validation-and-migration.md` |
| S42-003 | 定义 missing/unknown/schema_version 红灯测试 | Done | `tests/test_cli.py` |
| S42-004 | 实现 core record schema validation helpers | Done | `abh/models.py` |
| S42-005 | 接入 doctor malformed record reporting | Done | `abh/core.py`, `abh/roadmap.py` |
| S42-006 | 同步 roadmap、task-board 和 schema migration 策略说明 | Done | `docs/development-roadmap.md`, `docs/task-board.md` |
| S42-007 | plan-046 验证、独立审计和关闭 | Done | `.abh/verifications/ver-d4be20596e20.json`, `docs/audits/audit-046-schema-validation-and-migration-r2.md`, `docs/plans/plan-046-schema-validation-and-migration.md` |

## Sprint 43

目标：把 `stage6.verification-runner-trust-policy` dogfood 成 `plan-047-verification-runner-trust-policy`，明确 verify runner 的本地 shell trust boundary、runner policy metadata 和 recursive guard 覆盖。

| ID | 任务 | 状态 | 产出 |
| --- | --- | --- | --- |
| S43-001 | materialize Verification Runner Trust Policy 计划 | Done | `stage6.verification-runner-trust-policy` -> `docs/plans/plan-047-verification-runner-trust-policy.md` |
| S43-002 | 定义 verification runner trust policy 实施计划 | Done | `docs/superpowers/plans/2026-06-05-verification-runner-trust-policy.md` |
| S43-003 | 定义 runner policy metadata 和 recursive guard 红灯测试 | Done | `tests/test_cli.py` |
| S43-004 | 实现 runner policy metadata 与 recursive guard 增强 | Done | `abh/verifications.py` |
| S43-005 | 同步 README、roadmap 和 task-board trust policy 文档 | Done | `README.md`, `docs/development-roadmap.md`, `docs/task-board.md` |
| S43-006 | plan-047 验证、独立审计和关闭 | Done | `.abh/verifications/`, `docs/audits/`, `docs/plans/plan-047-verification-runner-trust-policy.md` |

## Sprint 44

目标：把 `stage6.test-suite-domain-split` dogfood 成 `plan-048-test-suite-domain-split`，把 monolithic unittest regression suite 拆成聚焦领域模块，并保留薄的端到端 CLI/MCP 覆盖。

| ID | 任务 | 状态 | 产出 |
| --- | --- | --- | --- |
| S44-001 | materialize Test Suite Domain Split 计划 | Done | `stage6.test-suite-domain-split` -> `docs/plans/plan-048-test-suite-domain-split.md` |
| S44-002 | 定义 test suite domain split 实施计划 | Done | `docs/superpowers/plans/2026-06-05-test-suite-domain-split.md` |
| S44-003 | 提取共享测试支撑与 focused module 边界 | Done | `tests/__init__.py`, `tests/support.py`, `tests/test_*.py` |
| S44-004 | 缩减 `tests/test_cli.py` 为薄 e2e CLI 层 | Done | `tests/test_cli.py` |
| S44-005 | 同步 codebase map、roadmap 和 task-board 测试面文档 | Done | `docs/context/codebase-map.md`, `docs/development-roadmap.md`, `docs/task-board.md` |
| S44-006 | plan-048 验证、独立审计和关闭 | Done | `.abh/verifications/`, `docs/audits/`, `docs/plans/plan-048-test-suite-domain-split.md` |

## Sprint 45

目标：把 `stage6.commitment-phase-state` dogfood 成 `plan-049-commitment-phase-state`，为 plan 增加稳定承诺、活跃变化压力、目标稳定态、转换证明和残余压力的显式结构。

| ID | 任务 | 状态 | 产出 |
| --- | --- | --- | --- |
| S45-001 | materialize Commitment Phase State 计划 | Done | `stage6.commitment-phase-state` -> `docs/plans/plan-049-commitment-phase-state.md` |
| S45-002 | 定义 commitment phase state 实施计划 | Done | `docs/superpowers/plans/2026-06-05-commitment-phase-state.md` |
| S45-003 | 定义 legacy/default/json/rendering 红灯测试 | Done | `tests/test_cli.py` |
| S45-004 | 实现 Commitment Phase State 模型、渲染和 CLI surface | Done | `abh/models.py`, `abh/plans.py`, `abh/cli.py` |
| S45-005 | 同步 plan template、quality-signals、roadmap、task-board 和 codebase map | Done | `docs/plans/templates/plan-template.md`, `docs/architecture/quality-signals.md`, `docs/development-roadmap.md`, `docs/task-board.md`, `docs/context/codebase-map.md` |
| S45-006 | plan-049 验证、独立审计和关闭 | Done | `.abh/verifications/`, `docs/audits/audit-049-commitment-phase-state.md`, `docs/plans/plan-049-commitment-phase-state.md` |

## Sprint 46

目标：把 `stage6.audit-semantic-conservation` dogfood 成 `plan-050-audit-semantic-conservation`，让 audit bundle 和审计文档显式检查语义承诺守恒，并区分 J-flow-only 路由证据与 R-flow 不确定性降低证据。

| ID | 任务 | 状态 | 产出 |
| --- | --- | --- | --- |
| S46-001 | materialize Audit Semantic Conservation 计划 | Done | `stage6.audit-semantic-conservation` -> `docs/plans/plan-050-audit-semantic-conservation.md` |
| S46-002 | 补齐 plan-050 定义并转入 ready/running | Done | `docs/plans/plan-050-audit-semantic-conservation.md` |
| S46-003 | 定义 audit bundle prompt 内容红灯测试 | Done | `tests/test_verifications_and_audits.py` |
| S46-004 | 实现 semantic conservation 与 J-flow/R-flow 审计提示 | Done | `abh/audit_bundle.py` |
| S46-005 | 同步 audit template、audits README、quality signals、roadmap、task-board 和 codebase map | Done | `docs/audits/templates/audit-template.md`, `docs/audits/README.md`, `docs/architecture/quality-signals.md`, `docs/development-roadmap.md`, `docs/task-board.md`, `docs/context/codebase-map.md` |
| S46-006 | plan-050 验证、独立审计和关闭 | Done | `.abh/verifications/ver-850d3e65452b.json`, `docs/audits/audit-050-audit-semantic-conservation-r2.md`, `docs/plans/plan-050-audit-semantic-conservation.md` |

## Sprint 47

目标：把 `stage6.owner-doc-stable-commitments` dogfood 成 `plan-051-owner-doc-stable-commitments`，让关键 owner docs、attractor 模板和 `abh init` seed 文档显式区分 Stable Commitments、Allowed Variation、Drift / Leakage Signals 和 Correction Path。

| ID | 任务 | 状态 | 产出 |
| --- | --- | --- | --- |
| S47-001 | materialize Owner Doc Stable Commitments 计划 | Done | `stage6.owner-doc-stable-commitments` -> `docs/plans/plan-051-owner-doc-stable-commitments.md` |
| S47-002 | 补齐 plan-051 定义并转入 ready/running | Done | `docs/plans/plan-051-owner-doc-stable-commitments.md` |
| S47-003 | 定义 owner-doc stable commitments 红灯测试 | Done | `tests/test_command_contracts.py` |
| S47-004 | 更新当前 owner docs、attractor 模板和 init seed 文档 | Done | `docs/index.md`, `docs/context/source-of-truth.md`, `docs/context/project-context.md`, `docs/context/codebase-map.md`, `docs/architecture/templates/attractor-template.md`, `abh/init.py` |
| S47-005 | 同步 quality signals、roadmap、task-board 和 codebase map | Done | `docs/architecture/quality-signals.md`, `docs/development-roadmap.md`, `docs/task-board.md`, `docs/context/codebase-map.md` |
| S47-006 | plan-051 验证、独立审计和关闭 | Done | `.abh/verifications/ver-726c18a5135b.json`, `docs/audits/audit-051-owner-doc-stable-commitments.md`, `docs/plans/plan-051-owner-doc-stable-commitments.md` |

## Sprint 48

目标：把 `stage6.post-close-freshness-semantics` dogfood 成 `plan-052-post-close-freshness-semantics`，区分 close-gate freshness 与 post-close health freshness，避免 closed plan 因 audit/close metadata churn 被误报为高危 stale proof。

| ID | 任务 | 状态 | 产出 |
| --- | --- | --- | --- |
| S48-001 | materialize Post-Close Freshness Semantics 计划 | Done | `stage6.post-close-freshness-semantics` -> `docs/plans/plan-052-post-close-freshness-semantics.md` |
| S48-002 | 补齐 plan-052 定义并转入 ready/running | Done | `docs/plans/plan-052-post-close-freshness-semantics.md` |
| S48-003 | 定义 closed-plan stale reason 与 health report 红灯测试 | Done | `tests/test_verifications_and_audits.py`, `tests/test_memory_drift_reporting.py`；覆盖 close audit-id bookkeeping、proof-bearing closure evidence、tracked roadmap/task-board sync 和其他 git drift |
| S48-004 | 实现 stale reason detail 与 post-close metadata churn health signal | Done | `abh/plans.py`, `abh/reporting.py`；仅 bounded post-close docs sync 与 close bookkeeping 降级为 governance churn |
| S48-005 | 同步 quality signals、roadmap、task-board 和 codebase map | Done | `docs/architecture/quality-signals.md`, `docs/development-roadmap.md`, `docs/task-board.md`, `docs/context/codebase-map.md` |
| S48-006 | plan-052 验证、独立审计和关闭 | Done | `.abh/verifications/ver-e55f64471acf.json`, `docs/audits/audit-052-post-close-freshness-semantics.md`, `docs/plans/plan-052-post-close-freshness-semantics.md` |

## Sprint 49

目标：把 `stage7.ci-templates` dogfood 成 `plan-053-ci-templates`，把现有 GitHub Actions 基础 CI 升级为可复用 ABH PR 检查模板，运行完整 unittest、doctor、roadmap、diff 和 health posture 检查，同时不实现发布自动化或团队策略。

| ID | 任务 | 状态 | 产出 |
| --- | --- | --- | --- |
| S49-001 | materialize CI Templates 计划 | Done | `stage7.ci-templates` -> `docs/plans/plan-053-ci-templates.md` |
| S49-002 | 补齐 plan-053 定义并转入 running | Done | `docs/plans/plan-053-ci-templates.md`, `.abh/roadmap.json` |
| S49-003 | 定义 CI workflow command contract 红灯测试 | Done | `tests/test_command_contracts.py` |
| S49-004 | 升级 GitHub Actions CI workflow | Done | `.github/workflows/ci.yml` |
| S49-005 | 同步 CI recipe、README、roadmap、task-board 和 codebase map | Done | `docs/recipes/ci.md`, `README.md`, `docs/development-roadmap.md`, `docs/task-board.md`, `docs/context/codebase-map.md` |
| S49-006 | plan-053 验证、独立审计和关闭 | Done | `.abh/verifications/ver-f07a468169c6.json`, `docs/audits/audit-053-ci-templates.md`, `docs/plans/plan-053-ci-templates.md` |
| S49-007 | 关闭后同步下一步焦点 | Done | `stage7.multi-repo-sharing`, `docs/development-roadmap.md`, `docs/task-board.md` |

## 阶段 7 后续计划（plan-054 ~ plan-067）

| ID | 计划 | 状态 | 关键产出 |
| --- | --- | --- | --- |
| plan-043 | Plan Reference Set | Closed（deferred） | `stage6.plan-reference-set` → `plan-043-plan-reference-set`（closed） |
| plan-054 | Multi Repo Sharing | Closed（audit rejected） | 缺少 R-flow 实现证据，待重新 materialize |
| plan-055 | ABH Workflow Skill | Done | `skills/abh-workflow` Codex skill |
| plan-056 | README Zero-Python Skill Onboarding | Done | README 零基础使用说明 |
| plan-057 | Codex Repo Toggle | Done | `abh codex on/off --write --confirm` |
| plan-058 | Verification Sandbox and Storage Hardening | Done | 验证沙箱隔离 + storage 硬化 |
| plan-060 | Signal Quality Hardening | Done | stale severity 重分类 + memory triage |
| plan-061 | Drift Detection Depth | Done | terminology drift 检测 + verify run 集成 |
| plan-062 | Phase A: Zero-Friction Agent UX | Done | smart defaults + `plan run`/`plan finish` |
| plan-063 | Phase B: Dashboard + Memory Injection | Done | `abh next` 全局感知 + memory 注入 |
| plan-064 | Phase C: Agent-to-Agent Audit | Done | Agent-to-Agent 审计协议 |
| plan-065 | Memory Active Injection | Done | `plan status` 自动注入相关 memory |
| plan-066 | Audit Protocol v2 | Done | 自包含审计包 |
| plan-067 | Plan Complete | Done | `abh plan complete` 端到端意图执行 |
