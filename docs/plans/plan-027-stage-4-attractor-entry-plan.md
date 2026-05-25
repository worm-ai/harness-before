# Plan: Stage 4 Agent-First Attractor Entry Plan

## Metadata

- ID: plan-027-stage-4-attractor-entry-plan
- Status: closed
- Attractor: docs/architecture/attractors/abh-core-attractor.md
- Baseline: v0.3.0 is released; Stage 4 has been reframed as Agent-First attractor entry, but architecture docs and task-board still need alignment.
- Owner: platform
- Created: 2026-05-25T14:44:23.639922+00:00
- Updated: 2026-05-25T15:45:49.590992+00:00

## Goals

- Define Agent-First Command Contract as the Stage 4 technical baseline.
- Update roadmap, phase plan, README, task-board, and Agent Protocol docs so Stage 4 consistently starts with agent-first attractor entry.
- Keep this slice documentation/governance-only with no runtime behavior changes.

## Non-Goals

- Do not implement abh attractor, abh init, abh agent setup, hooks, abh next, onboarding check, or package distribution in this slice.
- Do not change CLI/MCP behavior, schemas, state machines, close gates, storage format, or runtime algorithms.

## Exit Criteria

- docs/architecture/agent-protocol.md describes Agent-First Command Contract and separates human approval from Agent command execution.
- README, development-roadmap, 阶段规划, and task-board consistently identify Stage 4 as Agent-First attractor entry starting at plan-027.
- development-roadmap lists Stage 4 plan queue and P1 implementation order without splitting Attractor Registry into a later stage.
- python3 -m abh doctor passes.
- python3 -m unittest tests/test_cli.py -v passes.

## Validation Checklist

- python3 -m abh doctor
- python3 -m unittest tests/test_cli.py -v
- git diff --check
- python3 -m abh plan status plan-027-stage-4-attractor-entry-plan --json

## Closure Evidence

- docs/architecture/agent-protocol.md
- README.md
- docs/development-roadmap.md
- docs/task-board.md
- docs/阶段规划.md
- audit-027-stage-4-attractor-entry-plan

## Verification Runs

- ver-789e779e8498
- ver-dd4e1a8178a1
- ver-49c8fc69492a

## Audits

- audit-027-stage-4-attractor-entry-plan
