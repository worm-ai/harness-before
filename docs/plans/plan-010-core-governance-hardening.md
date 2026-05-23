# Plan: Core Governance Hardening

## Metadata

- ID: plan-010-core-governance-hardening
- Status: closed
- Attractor: docs/architecture/attractors/abh-core-attractor.md
- Baseline: docs/development-roadmap.md
- Owner: platform
- Created: 2026-05-23T12:41:45.251472+00:00
- Updated: 2026-05-23T13:39:13.834631+00:00

## Goals

- 清理 plan-200-demo 遗留 draft 状态噪音
- 为核心 JSON 对象加入 schema/version 兼容字段
- 建立 CI 配置运行 unittest、abh doctor 和基础 smoke test
- 明确包版本与 README 功能版本策略
- 把关闭后文档同步检查纳入治理门禁

## Non-Goals

- 不实现 verify run
- 不重构 core.py 模块拆分
- 不引入外部运行时依赖

## Exit Criteria

- plan-200-demo 不再出现在 abh plan list 且 doctor 通过
- 新建或更新的核心 JSON 对象包含 schema_version
- 存在 CI workflow 覆盖 unittest、abh doctor、abh --help、abh plan list
- README 或 roadmap 明确版本策略
- roadmap/task-board 反映 Sprint 10 和 plan-010 收口状态

## Validation Checklist

- python3 -m unittest tests/test_cli.py -v
- python3 -m abh doctor
- python3 -m abh --help
- python3 -m abh plan list

## Closure Evidence

- docs/plans/plan-010-core-governance-hardening.md
- docs/development-roadmap.md
- docs/task-board.md
- .github/workflows/ci.yml
- tests/test_cli.py
- audit-010-core-governance-hardening

## Verification Runs

- ver-f1cbb9241fa4
- ver-c7de28ecf616
- ver-53ea615f5238
- ver-f585e661836b

## Audits

- audit-010-core-governance-hardening
