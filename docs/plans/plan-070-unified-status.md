# Plan: Unified abh status --json dashboard

## Metadata

- ID: plan-070-unified-status
- Status: running
- Attractor: docs/architecture/attractors/abh-core-attractor.md
- Baseline: Agent currently needs 4 commands (next, health, doctor, roadmap check) to understand repo state.
- Owner: platform
- Created: 2026-06-16T10:18:54.488809+00:00
- Updated: 2026-06-16T10:19:17.878428+00:00

## Goals

- New abh status command outputs a unified JSON dashboard.
- Dashboard includes: next_action, health_posture, open_plans count, doctor_issues count, roadmap_queued count, active_alerts count.
- CLI and MCP both expose abh_status.
- Read-only — no writes, no confirm required.

## Non-Goals

- Do not remove or deprecate individual commands (next, health, doctor, etc.).
- Do not add interactive or TUI mode.
- Do not aggregate across multiple repos.

## Exit Criteria

- abh status --json returns a unified dashboard with all 6 fields.
- abh_status MCP tool is available and read-only.
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

- python3 -m pytest tests/test_command_contracts.py -v
- python3 -m pytest tests/test_mcp_server.py -v
- python3 -m abh doctor
- python3 -m abh roadmap check --json
- git diff --check

## Closure Evidence

- abh/navigation.py
- abh/cli.py
- abh/commands.py
- abh/mcp_server.py
- tests/test_command_contracts.py
- tests/test_mcp_server.py

## Reference Set

### Active Owner Docs

- abh/navigation.py
- abh/reporting.py
- abh/commands.py

### Live Code Routes

- abh/navigation.py
- abh/reporting.py
- abh/core.py

### Tests Baseline

- tests/test_navigation_and_roadmap.py

### Known Issues

- Agent needs 4 commands to understand repo state

## Verification Runs

-

## Audits

-
