# Plan: Memory Index

## Metadata

- ID: plan-041-memory-index
- Status: closed
- Attractor: docs/architecture/attractors/abh-core-attractor.md
- Baseline: Current memory supports add/list/search by type and keyword. Stage 6 needs memory records that can say whether an experience is still active, what it relates to, and when an agent should reuse it.
- Owner: platform
- Created: 2026-05-30T07:57:01.140081+00:00
- Updated: 2026-05-30T08:45:55.491912+00:00

## Goals

- Add memory metadata for tags, status, related plans, related audits, related drift reports, and supersession.
- Preserve backward-compatible reads for existing memory records.
- Improve memory search/list output so agents can find reusable experience by relation and status, not only keyword.
- Document how memory quality signals feed route ranking, health reports, and abh next recommendations.

## Non-Goals

- Do not introduce vector search, embeddings, databases, or external services.
- Do not migrate or rewrite all historical memory documents in this slice.
- Do not implement health reports, team policy, or multi-repo sharing yet.

## Exit Criteria

- Memory JSON supports tags, status, related plan/audit/drift ids, and superseded_by with legacy defaults.
- abh memory add can record the new metadata without breaking existing flags.
- abh memory search/list --json can filter or expose status and relationship metadata.
- Tests cover legacy reads, new metadata writes, search/list JSON, and Markdown rendering.

## Validation Checklist

- python3 -m unittest tests/test_cli.py -v
- python3 -m abh doctor
- git diff --check
- python3 -m abh roadmap check --json

## Closure Evidence

- abh/models.py
- abh/memory.py
- abh/cli.py
- abh/mcp_server.py
- tests/test_cli.py
- README.md
- docs/architecture/quality-signals.md
- docs/development-roadmap.md
- docs/task-board.md
- docs/context/codebase-map.md
- abh/commands.py
- docs/architecture/agent-protocol.md
- .abh/roadmap.json
- docs/plans/plan-041-memory-index.md
- audit-041-memory-index

## Verification Runs

- ver-8bc3c90c3ffe
- ver-eee5e8ff79a7
- ver-543729974fde

## Audits

- audit-041-memory-index
