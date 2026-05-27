# Plan: Truth Precedence and AGE Docs Baseline

## Metadata

- ID: plan-031-truth-precedence-and-age-docs
- Status: closed
- Attractor: docs/architecture/attractors/abh-core-attractor.md
- Baseline: The AGE template review identified truth precedence, docs/index routing, docs/context, docs/requirements, and docs/design as prerequisites for an AGE-ready ABH init flow. ABH already has active attractor, Agent-First command contracts, Attractor Registry, and roadmap queue, but it lacks explicit source-of-truth precedence and stable AGE owner-doc baseline files.
- Owner: platform
- Created: 2026-05-27T04:46:24.079708+00:00
- Updated: 2026-05-27T04:54:42.661305+00:00

## Goals

- Define ABH source-of-truth precedence for requirements, design, architecture, code/schema, plans, audits, memory, and logs.
- Introduce stable AGE owner-doc entry points: docs/index.md and docs/context/ source-of-truth/project-context/conventions/codebase-map files.
- Update Stage 4 roadmap and Agent Protocol docs so abh init, agent setup, abh next, and onboarding check consume the AGE owner-doc baseline.
- Keep this slice focused on planning and stable docs; later slices implement init, next, onboarding, hooks, and memory type extensions.

## Non-Goals

- Do not implement abh init, agent setup, hooks, abh next, onboarding check, route ranking, or memory type changes in this slice.
- Do not weaken the existing plan close audit gate or introduce minor plans that skip audit.
- Do not change CLI/MCP runtime behavior beyond roadmap/doctor-compatible documentation and queue state.

## Exit Criteria

- docs/index.md exists and routes common Agent questions to the correct owner docs.
- docs/context/source-of-truth.md defines conflict resolution and source-of-truth precedence by question type.
- docs/context/project-context.md, docs/context/conventions.md, and docs/context/codebase-map.md exist with ABH-specific baseline content.
- development-roadmap and Agent Protocol mention the AGE owner-doc baseline as a prerequisite consumed by abh init and future agent navigation.
- python3 -m unittest tests/test_cli.py -v passes.
- python3 -m abh doctor passes.
- python3 -m abh roadmap check --json passes.

## Validation Checklist

- python3 -m unittest tests/test_cli.py -v
- python3 -m abh doctor
- python3 -m abh roadmap check --json
- git diff --check

## Closure Evidence

- docs/index.md
- docs/context/source-of-truth.md
- docs/context/project-context.md
- docs/context/conventions.md
- docs/context/codebase-map.md
- docs/development-roadmap.md
- docs/architecture/agent-protocol.md
- .abh/roadmap.json
- audit-031-truth-precedence-and-age-docs

## Verification Runs

- ver-00a6f1970a09
- ver-a628d91e3765

## Audits

- audit-031-truth-precedence-and-age-docs
