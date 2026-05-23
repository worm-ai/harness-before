# Plan: Agent Protocol Foundation

## Metadata

- ID: plan-012-agent-protocol-foundation
- Status: closed
- Attractor: docs/architecture/attractors/abh-core-attractor.md
- Baseline: docs/development-roadmap.md
- Owner: platform
- Created: 2026-05-23T15:57:16.505508+00:00
- Updated: 2026-05-23T16:08:03.463542+00:00

## Goals

- 将阶段规划和 roadmap 调整为阶段 2 Agent Protocol 优先
- 定义 Agent Protocol 最小协议边界、对象范围、错误模型和 MCP 分阶段策略
- 同步 task-board，使 Sprint 12 指向 Agent Protocol Foundation

## Non-Goals

- 不实现 JSON 输出模式
- 不实现 MCP Server
- 不开放 Agent 写操作
- 不实现 verify run

## Exit Criteria

- docs/阶段规划.md 和 docs/development-roadmap.md 均明确阶段 2 为 Agent Protocol 基础
- 新增 Agent Protocol 基线文档，覆盖 JSON 输出、Agent tool schema、错误模型、MCP 只读优先和写操作门禁
- docs/task-board.md 当前阶段和 Sprint 12 任务反映 plan-012
- doctor、单元测试和 plan list 均通过

## Validation Checklist

- python3 -m unittest tests/test_cli.py -v
- python3 -m abh doctor
- python3 -m abh plan list
- rg -n 'plan-012-agent-protocol-foundation|Agent Protocol' docs/development-roadmap.md docs/阶段规划.md docs/task-board.md docs/architecture/agent-protocol.md

## Closure Evidence

- docs/plans/plan-012-agent-protocol-foundation.md
- docs/architecture/agent-protocol.md
- docs/development-roadmap.md
- docs/阶段规划.md
- docs/task-board.md
- audit-012-agent-protocol-foundation

## Verification Runs

- ver-2f23b145ced9

## Audits

- audit-012-agent-protocol-foundation
