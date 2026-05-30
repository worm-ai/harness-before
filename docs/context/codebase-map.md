# Codebase Map

## Runtime Package

- `abh/cli.py` — argparse CLI adapter and human/JSON output handlers.
- `abh/commands.py` — Agent-First command contract, JSON envelope helpers, MCP tool metadata.
- `abh/agent_setup.py` — read-only setup bundle export for Codex, Claude Code, and generic MCP clients.
- `abh/hooks.py` — local hook guardrail profile preview and managed pre-commit installation.
- `abh/init.py` — `abh init` preview/write planning, AGE owner-doc templates, and default active attractor seeding.
- `abh/navigation.py` — read-only next-action recommendation and onboarding readiness checks.
- `abh/audit_bundle.py` — read-only audit prompt and evidence bundle generation.
- `abh/models.py` — schema-versioned records for attractors, plans, verifications, audits, memory, drift, and roadmap queue items.
- `abh/storage.py` — path helpers, workspace directories, atomic text/JSON writes, and local file locks.
- `abh/core.py` — compatibility re-export layer plus workspace doctor.

## Domain Modules

- `abh/attractors.py` — active attractor registry, creation, supersession, Markdown rendering.
- `abh/plans.py` — plan creation, update, transition, ready validation, close gate.
- `abh/verifications.py` — manual verification records and local validation runner.
- `abh/audits.py` — audit request, record, reviewer metadata, rendering, and parsing.
- `abh/audit_bundle.py` — audit bundle assembly from plan, verification, audit, and closure evidence state.
- `abh/memory.py` — externalized memory records, metadata indexing, relationship filters, Markdown rendering, and search.
- `abh/drift.py` — drift report creation, local rule-based analysis, and Stage 6 drift quality signal metadata.
- `abh/routing.py` — reading-order suggestions for questions.
- `abh/roadmap.py` — stable roadmap queue, next plan id calculation, materialization, and numbering checks.
- `abh/mcp_server.py` — MCP stdio adapter over the shared command contract and domain functions.

Stage 6 quality work starts with `docs/architecture/quality-signals.md`. Runtime modules should consume that vocabulary before adding new drift, memory, route, `abh next`, or reporting fields.

## Test Surface

- `tests/test_cli.py` is the main regression suite. It covers CLI behavior, JSON envelopes, MCP contracts, roadmap queue behavior, active attractor checks, verification metadata, atomic writes, and doctor checks.

## Onboarding Docs

- `docs/quickstart.md` — five-minute Agent-First entry path.
- `docs/recipes/` — Codex, Claude Code, MCP, hooks, first-loop, and distribution recipes.

## Primary Command Families

- `abh attractor ...`
- `abh agent setup ...`
- `abh hooks profile`
- `abh hooks install`
- `abh init`
- `abh next`
- `abh onboarding check`
- `abh plan ...`
- `abh verify ...`
- `abh audit ...`
- `abh close ...`
- `abh memory ...`
- `abh drift ...`
- `abh roadmap ...`
- `abh route ...`
- `abh doctor`

Future agent-facing command families should extend `abh.commands` before or alongside their CLI/MCP adapters. Stage 4 command families are complete: `agent setup` is a read-only export surface; write/install behavior for agent config files remains a later confirmed-write slice. `hooks install` is the first local hook write surface and requires `--write --confirm`; it only manages `.git/hooks/pre-commit` files containing the ABH managed marker. `next` and `onboarding check` are read-only navigation surfaces and must not install hooks or write Agent config. Quickstart and recipes are documentation-only adoption surfaces; PyPI publication and release automation remain future work. `audit bundle` is a Stage 5 read-only audit preparation surface; it must not call models, record verdicts, transition plans, or close plans. `audit record` now carries declared reviewer context, independence, and verification basis metadata; `close` enforces an independent passing audit tied to the current fresh passing verification. Stage 6 should stay product-quality-first and agent-navigation-second: drift findings now carry quality signal metadata, and memory records now carry tags, status, typed relationships, and supersession fields before route, `abh next`, and future health reports consume those signals conservatively.
