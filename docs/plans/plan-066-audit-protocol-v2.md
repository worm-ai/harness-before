# Plan: Audit Protocol v2: Self-Contained Audit Package

## Metadata

- ID: plan-066-audit-protocol-v2
- Status: closed
- Attractor: docs/architecture/attractors/abh-core-attractor.md
- Baseline: Auto-generated baseline. Recent commits: 34d2cd4 fix: _auto_reverify_if_git_only sentinel handling for non-git staleness; dc54be5 fix: extract auto-reverify into shared _auto_reverify_if_git_only; 53a9178 chore: remove stray test.md
- Owner: wangming
- Created: 2026-06-15T16:47:14.335948+00:00
- Updated: 2026-06-15T16:51:13.953936+00:00

## Goals

- audit bundle --protocol v2 outputs a self-contained audit package: plan goals/non-goals/exit-criteria + attractor invariants + changed files + diff summary + verification breakdown + related memories + self-check results.
- Self-check section pre-validates: exit criteria coverage, non-goal compliance, scope boundary, closure evidence completeness.
- Audit agent can produce verdict with <=5 tool calls after receiving the package (vs 20+ today).

## Non-Goals

- Do not remove v1 protocol — v2 is additive.

## Exit Criteria

- audit bundle --protocol outputs package with all required sections.
- Self-check correctly identifies exit criteria gaps, non-goal violations, and scope issues.
- Package is valid JSON consumable by an independent audit agent.

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

- abh/cli.py
- abh/audit_bundle.py
- abh/boundary.py
- audit-066-audit-protocol-v2

## Reference Set

-

## Verification Runs

- ver-ee7408e076c8

## Audits

- audit-066-audit-protocol-v2
