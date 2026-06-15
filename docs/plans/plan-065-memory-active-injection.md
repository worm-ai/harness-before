# Plan: Memory Active Injection: plan status auto-surfaces related memories

## Metadata

- ID: plan-065-memory-active-injection
- Status: closed
- Attractor: docs/architecture/attractors/abh-core-attractor.md
- Baseline: Auto-generated baseline. Recent commits: 34d2cd4 fix: _auto_reverify_if_git_only sentinel handling for non-git staleness; dc54be5 fix: extract auto-reverify into shared _auto_reverify_if_git_only; 53a9178 chore: remove stray test.md
- Owner: wangming
- Created: 2026-06-15T16:47:05.096541+00:00
- Updated: 2026-06-15T16:51:06.282269+00:00

## Goals

- abh plan status and MCP abh_plan_status automatically include related memories in response, not as optional hint but as first-class field.
- Related memories are matched by keyword overlap between plan goals/non-goals and memory summary+context.
- When related memories exist, response includes a 'warnings' field with actionable guidance (e.g. '⚠ mem-doc-sync-001: 修改 CLI 后检查 docs/ 同步').

## Non-Goals

- Do not change memory storage format.
- Do not require the agent to opt-in — injection is automatic.

## Exit Criteria

- plan status --json response includes 'related_memories' array with id, summary, relevance fields.
- plan status --json response includes 'warnings' array when related memories found.
- MCP abh_plan_status returns the same enriched response.
- Legacy plan status consumers (no related memories) receive empty arrays, not errors.

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
- abh/navigation.py
- abh/cli.py
- abh/mcp_server.py
- audit-065-memory-active-injection

## Reference Set

-

## Verification Runs

- ver-66f6d782a25e

## Audits

- audit-065-memory-active-injection
