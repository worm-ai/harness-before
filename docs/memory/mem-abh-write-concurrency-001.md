# Memory: Avoid parallel ABH write commands against the same object

## Metadata

- ID: mem-abh-write-concurrency-001
- Type: divergent_pattern
- Status: dismissed
- Tags: concurrency
- Created: 2026-05-24T11:07:14.039717+00:00
- Updated: 2026-06-15T15:05:32.756811+00:00
- Related:
- Related Plans:
- Related Audits:
- Related Drift Reports:
- Superseded By:

## Summary

Avoid parallel ABH write commands against the same object

## Context

During plan-019 dogfooding, plan transition and plan update were launched in parallel against plan-019. Both commands rewrote the same plan JSON/Markdown files without locking, leaving duplicated trailing fragments and causing JSONDecodeError: Extra data when reading the plan.

## Evidence

- .abh/plans/plan-019-verification-environment-metadata.json
- docs/plans/plan-019-verification-environment-metadata.md
- abh/storage.py

## Implication

Until ABH writes are atomic or locked, dogfooding agents should run ABH write commands sequentially for the same object. A future hardening plan should add atomic write or file-lock protection around write_json and Markdown render writes.

## Deprecation Policy

Mark deprecated when evidence no longer applies.
