# Codebase Map

## Runtime Package

- `abh/cli.py` — argparse CLI adapter and human/JSON output handlers.
- `abh/commands.py` — Agent-First command contract, JSON envelope helpers, MCP tool metadata.
- `abh/models.py` — schema-versioned records for attractors, plans, verifications, audits, memory, drift, and roadmap queue items.
- `abh/storage.py` — path helpers, workspace directories, atomic text/JSON writes, and local file locks.
- `abh/core.py` — compatibility re-export layer plus workspace doctor.

## Domain Modules

- `abh/attractors.py` — active attractor registry, creation, supersession, Markdown rendering.
- `abh/plans.py` — plan creation, update, transition, ready validation, close gate.
- `abh/verifications.py` — manual verification records and local validation runner.
- `abh/audits.py` — audit request, record, rendering, and parsing.
- `abh/memory.py` — externalized memory records and search.
- `abh/drift.py` — drift report creation and simple rule-based analysis.
- `abh/routing.py` — reading-order suggestions for questions.
- `abh/roadmap.py` — stable roadmap queue, next plan id calculation, materialization, and numbering checks.
- `abh/mcp_server.py` — MCP stdio adapter over the shared command contract and domain functions.

## Test Surface

- `tests/test_cli.py` is the main regression suite. It covers CLI behavior, JSON envelopes, MCP contracts, roadmap queue behavior, active attractor checks, verification metadata, atomic writes, and doctor checks.

## Primary Command Families

- `abh attractor ...`
- `abh plan ...`
- `abh verify ...`
- `abh audit ...`
- `abh close ...`
- `abh memory ...`
- `abh drift ...`
- `abh roadmap ...`
- `abh route ...`
- `abh doctor`

Future Stage 4 command families should extend `abh.commands` before or alongside their CLI/MCP adapters.
