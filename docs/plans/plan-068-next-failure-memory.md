# Plan: abh next injects failure memory warnings

## Metadata

- ID: plan-068-next-failure-memory
- Status: running
- Attractor: docs/architecture/attractors/abh-core-attractor.md
- Baseline: plan-065 already injects memories into plan status; this extends injection to abh next recommendations.
- Owner: platform
- Created: 2026-06-16T03:46:59.708445+00:00
- Updated: 2026-06-16T10:18:32.583618+00:00

## Goals

- abh next searches memory for records related to the recommended roadmap key before returning a recommendation.
- When a failure memory is found, abh next includes a warnings field with memory summary and id.
- The recommendation itself is unchanged; the Agent can still proceed, but is now informed.

## Non-Goals

- Do not block or skip roadmap items automatically based on memory.
- Do not change the materialize flow itself.
- Do not implement full semantic search — keyword/ID matching is sufficient.

## Exit Criteria

- abh next --json returns warnings when recommending stage7.multi-repo-sharing (mem-audit-audit-054 present).
- python3 -m pytest tests/ -q passes.
- python3 -m abh doctor passes.

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

- python3 -m pytest tests/test_navigation_and_roadmap.py -v
- python3 -m abh doctor
- python3 -m abh roadmap check --json
- git diff --check

## Closure Evidence

- abh/navigation.py
- tests/test_navigation_and_roadmap.py
- .abh/roadmap.json

## Reference Set

### Active Owner Docs

- abh/navigation.py
- abh/memory.py

### Live Code Routes

- abh/navigation.py:recommend_next_action

### Tests Baseline

- tests/test_navigation_and_roadmap.py

### Known Issues

- plan-054 audit rejected — memory mem-audit-audit-054-multi-repo-sharing exists

## Verification Runs

- ver-6d6cecfd4c5f
- ver-ce26ea902c29
- ver-6c56bcf6f1d1
- ver-8507559b8094
- ver-587445da3c01

## Audits

-
