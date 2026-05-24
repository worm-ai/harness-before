# Attractor Before Harness 任务看板

## 当前阶段

Sprint 13：阶段 3 Verify Runner MVP（已完成）

## 状态说明

- Todo：尚未开始。
- Doing：正在进行。
- Review：等待审查或验收。
- Done：已完成。

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
