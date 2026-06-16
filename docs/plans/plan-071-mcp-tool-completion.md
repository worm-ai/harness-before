# Plan: MCP tool completion: next, onboarding_check, verify_run, audit_bundle

## Metadata

- ID: plan-071-mcp-tool-completion
- Status: running
- Attractor: docs/architecture/attractors/abh-core-attractor.md
- Baseline: 5 critical CLI commands lack MCP tool counterparts, violating the Agent-First CLI/MCP dual-interface invariant.
- Owner: platform
- Created: 2026-06-16T10:18:54.653139+00:00
- Updated: 2026-06-16T10:19:18.139945+00:00

## Goals

- New MCP tools: abh_next (read-only), abh_onboarding_check (read-only), abh_verify_run (write, confirm), abh_audit_bundle (read-only).
- All reuse existing core functions — no new business logic in MCP layer.
- Contracts registered in commands.py with mcp_tool field set.

## Non-Goals

- Do not add abh_agent_setup MCP tool (setup bundles are repo-init actions, not runtime governance).
- Do not change CLI behavior.
- Do not add write tools beyond verify_run.

## Exit Criteria

- abh_next MCP tool returns same data as abh next --json.
- abh_onboarding_check MCP tool returns readiness checks.
- abh_verify_run MCP tool executes plan validation commands with confirm=true.
- abh_audit_bundle MCP tool returns audit prompt + evidence.
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

- python3 -m pytest tests/test_mcp_server.py -v
- python3 -m pytest tests/test_command_contracts.py -v
- python3 -m abh doctor
- python3 -m abh roadmap check --json
- git diff --check

## Closure Evidence

- abh/mcp_server.py
- abh/commands.py
- tests/test_mcp_server.py
- tests/test_command_contracts.py

## Reference Set

### Active Owner Docs

- abh/mcp_server.py
- abh/commands.py

### Live Code Routes

- abh/mcp_server.py
- abh/commands.py

### Tests Baseline

- tests/test_mcp_server.py

### Known Issues

- 5 MCP tools missing — agents cannot complete full loop via MCP only

## Verification Runs

-

## Audits

-
