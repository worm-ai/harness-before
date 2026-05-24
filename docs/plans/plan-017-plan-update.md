# Plan: Plan Update MVP

## Metadata

- ID: plan-017-plan-update
- Status: closed
- Attractor: docs/architecture/attractors/abh-core-attractor.md
- Baseline: docs/development-roadmap.md
- Owner: platform
- Created: 2026-05-24T07:41:54.586538+00:00
- Updated: 2026-05-24T08:52:28.496879+00:00

## Goals

- 实现 abh plan update <plan_id>，支持通过 CLI 追加计划内容并保持 JSON/Markdown 双写一致
- 支持追加 goals、non-goals、exit criteria、validation checklist 和 closure evidence
- 避免重复追加同一条计划内容
- 支持移除错误的 validation checklist 条目以修复 dogfood 中发现的递归自调用阻塞

## Non-Goals

- 不实现删除、替换或重排计划字段
- 不新增交互式编辑器
- 不新增 MCP plan update 写工具
- 不修改 plan 状态机或关闭门禁

## Exit Criteria

- abh plan update <plan_id> 可追加 goal/non-goal/exit-criterion/validation/closure-evidence
- update 后 .abh/plans JSON 与 docs/plans Markdown 同步更新
- 重复传入同一条内容不会制造重复条目
- plan update 支持 --json 输出统一 envelope
- README、roadmap、task-board 同步 plan-017 状态
- plan update dogfoods itself without duplicating repeated closure evidence
- plan update can remove a validation checklist entry when dogfood finds it unsafe

## Validation Checklist

- python3 -m unittest tests/test_cli.py -v
- python3 -m abh doctor
- python3 -m abh plan update plan-017-plan-update --closure-evidence docs/plans/plan-017-plan-update.md --json

## Closure Evidence

- abh/core.py
- abh/cli.py
- tests/test_cli.py
- README.md
- docs/development-roadmap.md
- docs/task-board.md
- docs/plans/plan-017-plan-update.md
- docs/memory/mem-verify-runner-recursion-001.md
- audit-017-plan-update

## Verification Runs

- ver-37d33af3d107
- ver-2b2e7ba94c60
- ver-0d744683fda6
- ver-ebcdce56efe3
- ver-ee728ac51e7b
- ver-def6b34705f8
- ver-a7c67b85d9d1

## Audits

- audit-017-plan-update
