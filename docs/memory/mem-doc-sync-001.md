# Memory: 代码变更后文档同步反复遗漏

## Metadata

- ID: mem-doc-sync-001
- Type: divergent_pattern
- Status: active
- Created: 2026-05-22T16:45:06.134169+00:00
- Updated: 2026-05-22T16:45:06.134464+00:00
- Related:

## Summary

代码变更后文档同步反复遗漏

## Context

task-board.md 止于 Sprint 5（当前进度已到 Sprint 7），README 也曾缺失 list 命令和 route/drift 增强说明。每次 Sprint 结束时，文档同步总是滞后于代码变更。

## Evidence

- docs/task-board.md
- docs/plans/plan-007-sprint-7-dogfood.md

## Implication

每个 Sprint 关闭前必须显式检查 docs/ 下所有文档是否需要同步更新

## Deprecation Policy

Mark deprecated when evidence no longer applies.
