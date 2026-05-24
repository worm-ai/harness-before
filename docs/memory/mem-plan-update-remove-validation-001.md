# Memory: append-only plan update cannot repair unsafe validation checklist entries

## Metadata

- ID: mem-plan-update-remove-validation-001
- Type: divergent_pattern
- Status: active
- Created: 2026-05-24T08:28:20.821800+00:00
- Updated: 2026-05-24T08:28:20.821994+00:00
- Related: plan-017-plan-update, mem-verify-runner-recursion-001

## Summary

append-only plan update cannot repair unsafe validation checklist entries

## Context

During plan-017 dogfooding, append-only plan update could add evidence and validations but could not remove a recursive verify run checklist entry. The plan became blocked until a narrow --remove-validation capability was added.

## Evidence

- docs/plans/plan-017-plan-update.md
- .abh/verifications/ver-37d33af3d107.json
- abh/cli.py
- abh/core.py

## Implication

Plan update needs a constrained repair path for validation checklist entries, while still avoiding broad delete/replace/reorder semantics in the MVP.

## Deprecation Policy

Mark deprecated when evidence no longer applies.
