# Core Governance Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete stage-1 governance hardening by removing demo plan noise, adding object schema versioning, adding CI checks, and documenting version and post-close sync policy.

**Architecture:** Keep the changes local and Git-native. Add schema version compatibility to dataclass serialization/deserialization, harden tests around new records, remove the stale demo plan runtime records, and add a minimal GitHub Actions workflow that uses existing commands.

**Tech Stack:** Python standard library, unittest, argparse CLI, GitHub Actions YAML, repository-local JSON/Markdown records.

---

### Task 1: Schema Version Compatibility

**Files:**
- Modify: `abh/models.py`
- Modify: `tests/test_cli.py`

- [ ] Write failing tests that new plan/audit/memory/drift/verification JSON contains `schema_version`.
- [ ] Run focused tests and confirm RED.
- [ ] Add `SCHEMA_VERSION = "1"` and serialize `schema_version` in each model.
- [ ] Keep `from_dict` backward compatible for old JSON without `schema_version`.
- [ ] Run focused tests and full unittest suite.

### Task 2: Demo Plan Cleanup

**Files:**
- Delete: `.abh/plans/plan-200-demo.json`
- Delete: `.abh/verifications/ver-36387d5bc286.json`
- Ensure absent: `docs/plans/plan-200-demo.md`

- [ ] Remove the stale demo plan JSON and its verification JSON.
- [ ] Run `python3 -m abh plan list` and confirm `plan-200-demo` is absent.
- [ ] Run `python3 -m abh doctor` and confirm it passes.

### Task 3: CI And Version Policy

**Files:**
- Create: `.github/workflows/ci.yml`
- Modify: `README.md`
- Modify: `docs/development-roadmap.md`
- Modify: `docs/task-board.md`

- [ ] Add CI workflow for unittest, `abh doctor`, `abh --help`, and `abh plan list`.
- [ ] Document that package version, `abh.__version__`, and README feature claims must move together.
- [ ] Update roadmap/task-board to Sprint 10 and plan-010 closure state.
- [ ] Include post-close document sync as a closing gate, based on `mem-post-close-doc-sync-001`.

### Task 4: Verification And ABH Closure

**Files:**
- Modify: `.abh/plans/plan-010-core-governance-hardening.json`
- Modify: `docs/plans/plan-010-core-governance-hardening.md`
- Create: `docs/audits/audit-010-core-governance-hardening.md`

- [ ] Run full verification commands.
- [ ] Record verification runs.
- [ ] Request independent audit.
- [ ] Record audit result and close plan after pass.
