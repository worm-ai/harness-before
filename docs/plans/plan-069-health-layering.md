# Plan: Health report layers active vs historical pressure

## Metadata

- ID: plan-069-health-layering
- Status: blocked
- Attractor: docs/architecture/attractors/abh-core-attractor.md
- Baseline: Current health report shows 80 signals with no filtering — 76 are from closed plans.
- Owner: platform
- Created: 2026-06-16T09:44:08.099057+00:00
- Updated: 2026-06-16T10:18:34.524966+00:00

## Goals

- Health report splits pressure signals into active_pressure and historical_pressure lists.
- Metrics and posture are computed from active_pressure only.
- When no open plans exist, posture defaults to idle (not watch).
- --verbose flag includes historical_pressure in output.

## Non-Goals

- Do not delete or suppress historical signals — they remain accessible via --verbose.
- Do not change the severity or classification of individual signals.
- Do not add new signal types.

## Exit Criteria

- abh report health --json returns posture=idle when all plans are closed.
- active_pressure is empty when no open plans exist.
- historical_pressure contains closed-plan stale proofs.
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

- python3 -m pytest tests/test_memory_drift_reporting.py -v
- python3 -m abh doctor
- python3 -m abh roadmap check --json
- git diff --check

## Closure Evidence

- abh/reporting.py
- tests/test_memory_drift_reporting.py
- .abh/roadmap.json

## Reference Set

### Active Owner Docs

- abh/reporting.py

### Live Code Routes

- abh/reporting.py:project_health_report

### Tests Baseline

- tests/test_memory_drift_reporting.py

### Known Issues

- 80 pressure signals, 76 from closed plans — noise ratio 95%

## Verification Runs

- ver-9c3396cbfdeb
- ver-9ba509d1a259
- ver-d48d22dc627b

## Audits

-
