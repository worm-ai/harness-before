# Plan: Signal Quality Hardening

## Metadata

- ID: plan-060-signal-quality-hardening
- Status: blocked
- Attractor: docs/architecture/attractors/abh-core-attractor.md
- Baseline: Health report posture is at_risk but 59/74 signals are stale_proof from closed plans — noise masking real risks. 11/13 memories are orphaned with no triage tooling.
- Owner: platform
- Created: 2026-06-15T14:18:20.637515+00:00
- Updated: 2026-06-15T14:23:40.591219+00:00

## Goals

- Distinguish closed-plan stale_proof from open-plan in health report severity: closed-plan stale downgraded to info, open-plan stays high.
- Add 'abh memory triage' subcommand: interactive listing of orphaned memories with guided prompts to add tags, relate to plans/audits/drifts, or mark dismissed.
- Ensure health report posture calculation reflects true risk after stale_proof reclassification.

## Non-Goals

- Do not change memory storage format or add new memory types.
- Do not modify the existing abh memory add/search/list commands.
- Do not auto-fix orphaned memories — triage is human-guided.

## Exit Criteria

- Health report posture drops from at_risk to healthy after closed-plan stale_proof downgraded to info.
- abh memory triage lists orphaned memories with severity, prompts for next action per memory.
- abh memory triage --json returns machine-readable triage data.
- Tests cover stale severity classification and memory triage JSON output.

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

- abh/reporting.py
- abh/memory.py
- abh/cli.py
- abh/commands.py
- abh/models.py
- abh/navigation.py
- tests/test_cli.py

## Reference Set

-

## Verification Runs

- ver-db12cfe8c982
- ver-bfc825c02271

## Audits

-
