# Plan: Drift Detection Depth

## Metadata

- ID: plan-061-drift-detection-depth
- Status: running
- Attractor: docs/architecture/attractors/abh-core-attractor.md
- Baseline: Drift detection currently covers only import graph comparison and scope boundary checks. Terminology drift (plan terminology diverging from attractor glossary) is not detected. Drift check is a standalone CLI command, not integrated into verify run.
- Owner: platform
- Created: 2026-06-15T14:32:54.055170+00:00
- Updated: 2026-06-15T14:36:17.011048+00:00

## Goals

- Add terminology drift detection: compare plan goals/non-goals keywords against attractor-defined terms, flag inconsistent or diverging terminology.
- Integrate drift plan-check into verify run as an automatic post-validation step: run check_plan_scope + analyze_plan_drift after checklist commands, report drift findings as additional failure classifications.
- Ensure drift findings in verify run are visible in verification artifacts and failure_classifications without breaking existing verify behavior.

## Non-Goals

- Do not build a full NLP terminology system or external glossary database.
- Do not change the existing standalone drift plan-check CLI command.
- Do not auto-fix terminology drift — detection only.

## Exit Criteria

- analyze_terminology_drift detects when plan goals use terms inconsistent with attractor invariants or boundary rules.
- verify run automatically includes drift check results after executing validation checklist.
- Tests cover terminology drift detection and verify-run drift integration.

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

- abh/boundary.py
- abh/verifications.py
- abh/cli.py
- abh/models.py
- tests/test_boundary.py

## Reference Set

-

## Verification Runs

- ver-1030bb316abb
- ver-9e142437bab3
- ver-110ad8fe3b20
- ver-41a892047ffc

## Audits

-
