# Plan: Phase C: Agent-to-Agent Audit Protocol

## Metadata

- ID: plan-064-agent-ux-phase-c
- Status: running
- Attractor: docs/architecture/attractors/abh-core-attractor.md
- Baseline: Auto-generated baseline. Recent commits: 16b52fa feat(Phase B): dashboard + memory injection in abh next; 766e0e5 feat(Phase A): smart defaults + plan run/finish compound commands; 6de2da2 fix: address 3 code review findings
- Owner: wangming
- Created: 2026-06-15T16:31:05.841460+00:00
- Updated: 2026-06-15T16:31:13.513340+00:00

## Goals

- abh audit bundle --protocol outputs structured JSON instead of Markdown prompt, with explicit fields for plan goals, non-goals, exit criteria, evidence paths, and verification id.
- abh audit record --from-protocol <file.json> consumes a structured JSON verdict from the audit agent and records it directly.

## Non-Goals

- Do not remove the existing Markdown bundle — protocol is additive.

## Exit Criteria

- audit bundle --protocol outputs valid JSON with all fields required for an independent agent to audit.
- audit record --from-protocol accepts valid JSON verdict and records audit correctly.

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

- abh/audit_bundle.py
- abh/cli.py
- abh/audits.py

## Reference Set

-

## Verification Runs

-

## Audits

-
