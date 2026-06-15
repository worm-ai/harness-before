# Plan: Phase A: Zero-Friction Agent UX

## Metadata

- ID: plan-062-agent-ux-phase-a
- Status: running
- Attractor: docs/architecture/attractors/abh-core-attractor.md
- Baseline: Agent currently needs ~18 tool calls per plan lifecycle. Smart defaults and compound commands can cut this to ~12. Primary user is AI Agent, not human CLI operator.
- Owner: platform
- Created: 2026-06-15T15:32:17.318053+00:00
- Updated: 2026-06-15T15:32:22.212807+00:00

## Goals

- Smart defaults: plan create auto-detects active attractor, generates baseline from git status, uses standard validation checklist, infers owner from git config.
- Compound command 'abh plan run <id>': transitions draft→ready→running if needed, runs verification, returns result.
- Compound command 'abh plan finish <id>': pre-close completeness check (audit exists? verification fresh? scope ok?), fixes git-only staleness, outputs actionable next step.

## Non-Goals

- Do not remove existing fine-grained commands — compound commands are conveniences, not replacements.
- Do not auto-create plans without human/agent intent.
- Do not auto-close — human/agent must still confirm close.

## Exit Criteria

- plan create with only --id --title --goal succeeds with all other fields auto-populated.
- abh plan run <id> goes from draft/ready to running+verified in one command.
- abh plan finish <id> checks audit/verification/scope, auto-fixes git staleness, reports ready-to-close or blocker.
- Tests cover smart defaults, plan run, and plan finish.

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
- abh/plans.py
- abh/commands.py

## Reference Set

-

## Verification Runs

-

## Audits

-
