# Plan: Plan Reference Set

## Metadata

- ID: plan-043-plan-reference-set
- Status: closing
- Attractor: docs/architecture/attractors/abh-core-attractor.md
- Baseline: Plans currently declare attractor, baseline, goals, non-goals, exit criteria, validation checklist, and closure evidence, but they do not explicitly name the owner docs, code routes, tests, memory, drift, external contracts, and audit evidence that must be read for the slice.
- Owner: platform
- Created: 2026-05-30T12:08:07.774509+00:00
- Updated: 2026-06-14T16:51:18.874825+00:00

## Goals

- Add an optional Reference Set structure to plan JSON and Markdown rendering with backward-compatible defaults.
- Expose Reference Set data through plan status JSON, roadmap materialization, and plan update or creation flows without breaking existing plans.
- Update plan templates and documentation to distinguish active owner docs, live code routes, test baselines, known issues, external contracts, and plan/audit evidence.
- Document how future audit bundles, health reports, route ranking, and abh next can consume Reference Set entries.

## Non-Goals

- Do not make Reference Set mandatory for ready plans in the first slice.
- Do not implement embeddings, vector search, external documentation crawlers, or LLM-generated reference discovery.
- Do not change close semantics or audit independence gates.

## Exit Criteria

- New plans can carry a Reference Set in JSON and Markdown while legacy plans read with empty defaults.
- Plan status JSON exposes the Reference Set.
- Plan templates and docs explain the Reference Set categories and source-of-truth role.
- Tests cover legacy reads, new Reference Set rendering, JSON output, and roadmap materialization behavior.

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

- python3 -m unittest tests/test_cli.py -v
- python3 -m abh doctor
- git diff --check
- python3 -m abh roadmap check --json

## Closure Evidence

- abh/models.py
- abh/plans.py
- abh/cli.py
- abh/roadmap.py
- tests/test_cli.py
- docs/plans/templates/plan-template.md
- docs/architecture/quality-signals.md
- docs/development-roadmap.md
- docs/task-board.md
- docs/context/codebase-map.md
- docs/superpowers/plans/2026-05-30-plan-reference-set.md
- README.md
- abh/commands.py
- abh/mcp_server.py

## Reference Set

### Context Routing

- 

### Active Owner Docs

- 

### Live Code Routes

- 

### Tests Baseline

- 

### Known Issues

- 

### External Contracts

- 

### Plan Audit Evidence

- 

## Verification Runs

- ver-44f91f780ece

## Audits

- 
