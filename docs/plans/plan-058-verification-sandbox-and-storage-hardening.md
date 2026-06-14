# Plan: Verification Sandbox and Storage Hardening

## Metadata

- ID: plan-058-verification-sandbox-and-storage-hardening
- Status: closed
- Attractor: docs/architecture/attractors/abh-core-attractor.md
- Baseline: ABH v0.3.0 run_verification uses subprocess.run(shell=True) with no isolation or allowlisting; storage has no archival, pagination, or read-path locking; schema_version is 1 with no migration chain; tests are integration-only with a single test file.
- Owner: platform
- Created: 2026-06-14T05:36:01.794724+00:00
- Updated: 2026-06-14T09:29:58.040599+00:00

## Goals

- Add execution policy layer to verification runner with command allowlisting and resource limits
- Freeze closed plans against accidental mutation
- Add pagination support to list operations
- Add shared read locks to prevent JSON/Markdown tear during concurrent writes
- Add schema migration v1-to-v2 infrastructure with doctor --fix support
- Add unit test modules for drift, plans, storage, and verification

## Non-Goals

- Do not add Docker or container sandbox
- Do not change existing verification trust semantics for local_shell records
- Do not replace JSON file storage with a database
- Do not add MCP authentication

## Exit Criteria

- Verification commands can be allowlisted and blocked by policy
- Closed plans reject mutation attempts
- list operations support --limit and --offset pagination
- Read paths use shared locks
- Schema v1 records migrate to v2 on read
- Unit tests cover drift analysis, plan transitions, storage concurrency, verification policy

## Commitment Phase State

### Stable State Now

- CLI loop is stable with guarded_local_shell policy and read-path locks

### Active Change Pressure

- Need closed-plan immutability guard and schema migration in production

### Target Stable State

- Plans are frozen after close, reads are lock-protected, common verification commands are allowlisted

### Conversion Proof

- 

### Residual Pressure

- 

## Validation Checklist

- python3 -m unittest tests/test_cli.py -v
- python3 -m abh doctor
- python3 -m abh roadmap check --json
- git diff --check

## Closure Evidence

- abh/verifications.py
- abh/storage.py
- abh/plans.py
- abh/models.py
- tests/test_verification_policy.py
- tests/test_storage_concurrency.py
- tests/test_plans_unit.py
- tests/test_drift_unit.py
- audit-058b-dogfood-hardening-r2

## Verification Runs

- ver-ec5fe36ae7ff
- ver-75295d14680f
- ver-b4b62a1bd22e
- ver-845743bb049a
- ver-16edd0d00144

## Audits

- audit-058-dogfood-hardening
- audit-058b-dogfood-hardening-r2
