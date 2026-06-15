# Plan: abh plan complete: End-to-End Intent Execution

## Metadata

- ID: plan-067-plan-complete
- Status: closed
- Attractor: docs/architecture/attractors/abh-core-attractor.md
- Baseline: Auto-generated baseline. Recent commits: 34d2cd4 fix: _auto_reverify_if_git_only sentinel handling for non-git staleness; dc54be5 fix: extract auto-reverify into shared _auto_reverify_if_git_only; 53a9178 chore: remove stray test.md
- Owner: wangming
- Created: 2026-06-15T16:47:23.244076+00:00
- Updated: 2026-06-15T16:51:22.132926+00:00

## Goals

- Single MCP tool abh_plan_complete executes the full plan closing flow: verify freshness → check audit → auto-fix git staleness → scope check → close.
- Returns structured result: either {status: closed, plan: {...}} or {status: blocked, blockers: [...], recommendations: [...]}.
- Only pauses for human/agent when: audit not pass, product proof drift, or scope violation requiring explicit override.

## Non-Goals

- Do not bypass close_plan invariants — audit gate, closure evidence, and scope check remain enforced.

## Exit Criteria

- abh_plan_complete succeeds when plan has passing audit, fresh verification, clean scope, and complete evidence.
- abh_plan_complete returns structured blockers when any gate fails, with specific fix recommendations.
- MCP tool abh_plan_complete is registered and callable.

## Commitment Phase State

### Stable State Now

-

### Active Change Pressure

-

### Target Stable State

-

### Conversion Proof

-

### Residual Pressure

-

## Validation Checklist

- python3 -m pytest tests/ -q
- python3 -m abh doctor
- git diff --check

## Closure Evidence

- abh/plans.py
- abh/cli.py
- abh/mcp_server.py
- abh/commands.py
- audit-067-plan-complete

## Reference Set

-

## Verification Runs

- ver-353097eec123

## Audits

- audit-067-plan-complete
