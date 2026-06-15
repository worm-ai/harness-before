# Plan: Phase B: Global Awareness Dashboard + Memory Injection

## Metadata

- ID: plan-063-agent-ux-phase-b
- Status: closed
- Attractor: docs/architecture/attractors/abh-core-attractor.md
- Baseline: Auto-generated baseline. Recent commits: 766e0e5 feat(Phase A): smart defaults + plan run/finish compound commands; 6de2da2 fix: address 3 code review findings; e09f7d5 fix: auto-reverify on git-only staleness + add abh memory update command
- Owner: wangming
- Created: 2026-06-15T15:35:09.811892+00:00
- Updated: 2026-06-15T16:34:11.033435+00:00

## Goals

- Add 'abh dashboard' command: single-call overview replacing plan list + roadmap list + report health + memory triage.
- Memory injection in abh next: automatically surface related memories when recommending next actions.
- Memory injection in abh plan status: when viewing a plan, show related memories based on keyword overlap with plan goals/non-goals.

## Non-Goals

- Do not build a web dashboard or GUI — CLI and JSON output only.
- Do not implement full-text search or embeddings for memory matching.

## Exit Criteria

- abh dashboard shows posture, recent plans, queued roadmap, orphaned memories, and top signals in one screen.
- abh dashboard --json returns structured data consumable by agents.
- abh next references related memories when recommending actions.
- Tests cover dashboard JSON output and memory injection.

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
- abh/navigation.py
- abh/reporting.py
- abh/plans.py
- audit-063-agent-ux-phase-b

## Reference Set

-

## Verification Runs

- ver-f29dc67f92b9
- ver-1132923c8015

## Audits

- audit-063-agent-ux-phase-b
