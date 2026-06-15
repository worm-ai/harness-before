# Memory: Audit audit-043-plan-reference-set rejected plan plan-043-plan-reference-set: partial

## Metadata

- ID: mem-audit-audit-043-plan-reference-set
- Type: divergent_pattern
- Status: active
- Tags: auto-generated, audit-rejection, partial
- Created: 2026-06-15T00:54:47.719452+00:00
- Updated: 2026-06-15T00:54:47.719826+00:00
- Related: audit-043-plan-reference-set
- Related Plans: plan-043-plan-reference-set
- Related Audits: audit-043-plan-reference-set
- Related Drift Reports: 
- Superseded By: 

## Summary

Audit audit-043-plan-reference-set rejected plan plan-043-plan-reference-set: partial

## Context

Plan: Plan Reference Set (attractor: docs/architecture/attractors/abh-core-attractor.md). Auditor: claude-sonnet-4-6 independent audit. Independence: independent. Rationale: Goals G1-G3 and non-goals NG1-NG3 are satisfied. However, exit criterion EC4 is NOT met: zero tests for reference_set exist anywhere in tests/.

## Evidence

- docs/audits/audit-043-plan-reference-set.md

## Implication

Plan plan-043-plan-reference-set was rejected by independent audit. Missing reference_set tests (EC4). Add tests to tests/test_cli.py for legacy reads, JSON output, Markdown rendering, and roadmap materialization.

## Deprecation Policy

Mark deprecated when evidence no longer applies.
