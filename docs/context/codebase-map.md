# Codebase Map

## Runtime Package

- `abh/cli.py` — argparse CLI adapter and human/JSON output handlers.
- `abh/commands.py` — Agent-First command contract, JSON envelope helpers, MCP tool metadata.
- `abh/agent_setup.py` — read-only setup bundle export for Codex, Claude Code, and generic MCP clients.
- `abh/codex_setup.py` — preview, status, confirmed write, and managed removal for repository-local Codex ABH config.
- `abh/hooks.py` — local hook guardrail profile preview and managed pre-commit installation.
- `abh/init.py` — `abh init` preview/write planning, AGE owner-doc templates, and default active attractor seeding.
- `abh/navigation.py` — read-only next-action recommendation and onboarding readiness checks.
- `abh/audit_bundle.py` — read-only audit prompt and evidence bundle generation, including Stage 6 semantic conservation and J-flow/R-flow reviewer guidance.
- `abh/reporting.py` — read-only project health and semantic pressure aggregation over plans, verifications, audits, drift, memory, doctor, and roadmap queue state.
- `abh/models.py` — schema-versioned records for attractors, plans, Commitment Phase State, verifications, audits, memory, drift, and roadmap queue items.
- `abh/storage.py` — path helpers, workspace directories, atomic text/JSON writes, and local file locks.
- `abh/core.py` — compatibility re-export layer plus workspace doctor.
- `.github/workflows/ci.yml` — reusable GitHub Actions CI template for ABH pull-request checks.
- Stage 7 completed slice: `plan-053-ci-templates` owns the current CI template and CI recipe. Its drift boundary is roadmap consistency, whitespace drift, and read-only health posture; it does not run standalone `abh drift analyze`, release automation, branch protection, or team policy. `plan-054-multi-repo-sharing` is blocked/deferred after independent audit confirmed the plan definition exists but no import/export R-flow implementation evidence exists. `plan-055-abh-workflow-skill` is closed and packages existing ABH CLI workflow into `skills/abh-workflow` without implementing multi-repo sharing. `plan-057-codex-repo-toggle` is closed.

## Domain Modules

- `abh/attractors.py` — active attractor registry, creation, supersession, Markdown rendering.
- `abh/plans.py` — plan creation, update, Commitment Phase State rendering, transition, ready validation, close gate.
- `abh/verifications.py` — manual verification records and local validation runner.
- `abh/audits.py` — audit request, record, reviewer metadata, rendering, and parsing.
- `abh/audit_bundle.py` — audit bundle assembly from plan, verification, audit, closure evidence state, and semantic conservation review prompts.
- `abh/memory.py` — externalized memory records, metadata indexing, relationship filters, Markdown rendering, and search.
- `abh/drift.py` — drift report creation, local rule-based analysis, and Stage 6 drift quality signal metadata.
- `abh/routing.py` — reading-order suggestions for questions.
- `abh/roadmap.py` — stable roadmap queue, next plan id calculation, materialization, and numbering checks.
- `abh/mcp_server.py` — MCP stdio adapter over the shared command contract and domain functions.

Stage 6 quality work starts with `docs/architecture/quality-signals.md`. Runtime modules should consume that vocabulary before adding new drift, memory, route, `abh next`, or reporting fields. `plan-042-project-health-report` adds `abh/reporting.py` as the read-only health aggregation module and scopes health as a semantic pressure report rather than a single score.

## Test Surface

- `tests/test_cli.py` is now the thin end-to-end CLI regression layer for init/setup/hooks/attractor/plan smoke coverage and representative command-loop checks.
- `tests/test_mcp_server.py` covers MCP stdio transport, tool metadata, readonly reads, controlled writes, and MCP-specific close-gate flows.
- `tests/test_navigation_and_roadmap.py` covers `abh next`, onboarding readiness, roadmap numbering/materialization, and queue/blocked-plan navigation behavior.
- `tests/test_storage_and_doctor.py` covers workspace doctor consistency checks, schema issue reporting, atomic write behavior, and JSON/Markdown pair-writer coverage.
- `tests/test_models.py` covers schema-version serialization, validation, deprecated-field handling, and legacy record readability.
- `tests/test_verifications_and_audits.py` covers verification runner behavior, stale/trust metadata, recursive guard, audit record flows, audit bundle generation, close gates, and closed-plan stale field classification.
- `tests/test_memory_drift_reporting.py` covers memory indexing, route/drift behavior, and health-report aggregation, including post-close freshness health classification.
- `tests/test_command_contracts.py` covers shared command-contract metadata, JSON envelope behavior for read commands, CI workflow command coverage, and core re-export boundaries.
- `tests/support.py` provides the shared temporary-workspace, CLI, and MCP helper base classes used by focused test modules.

## Onboarding Docs

- `docs/quickstart.md` — five-minute Agent-First entry path.
- `docs/recipes/` — Codex, Claude Code, MCP, hooks, CI, first-loop, and distribution recipes.

## Primary Command Families

- `abh attractor ...`
- `abh agent setup ...`
- `abh hooks profile`
- `abh hooks install`
- `abh codex on|off|status`
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

Future agent-facing command families should extend `abh.commands` before or alongside their CLI/MCP adapters. Stage 4 command families are complete: `agent setup` is a read-only export surface; write/install behavior for agent config files remains a later confirmed-write slice. `hooks install` is the first local hook write surface and requires `--write --confirm`; it only manages `.git/hooks/pre-commit` files containing the ABH managed marker. `codex on|off` is a later confirmed-write slice with the same `--write --confirm` boundary and only manages ABH-owned `.codex/config.toml`. `next` and `onboarding check` are read-only navigation surfaces and must not install hooks or write Agent config. Quickstart and recipes are documentation-only adoption surfaces; PyPI publication and release automation remain future work. `audit bundle` is a Stage 5 read-only audit preparation surface; it must not call models, record verdicts, transition plans, or close plans. Stage 6 extends audit bundle prompts with semantic conservation and J-flow/R-flow reviewer guidance while preserving the read-only boundary. `audit record` now carries declared reviewer context, independence, and verification basis metadata; `close` enforces an independent passing audit tied to the current fresh passing verification. Stage 6 should stay product-quality-first and agent-navigation-second: drift findings now carry quality signal metadata, memory records now carry tags, status, typed relationships, and supersession fields, health reports should surface semantic pressure before route or `abh next` consume those signals conservatively, owner docs now expose stable commitments before future doctor gates inspect them, and `plan-052-post-close-freshness-semantics` closed with bounded post-close freshness semantics. Stage 7 started with closed `plan-053-ci-templates`; `plan-054-multi-repo-sharing` is blocked/deferred because it lacks actual sharing implementation evidence; `plan-055-abh-workflow-skill` is closed; `plan-057-codex-repo-toggle` is closed; multi-repo sharing, release automation, and team policy remain later slices.

## Stable Commitments

- Runtime command metadata lives in `abh.commands` and should be extended before CLI or MCP adapters diverge.
- `.abh/` stores machine-readable state; `docs/` stores human-readable mirrors and owner docs.
- `abh/init.py` owns seeded AGE owner-doc templates and default active attractor content for new workspaces.
- `abh/audit_bundle.py` stays read-only and must not record verdicts, transition plans, or close plans.
- `abh/reporting.py` reports semantic pressure without claiming automated semantic proof.

## Allowed Variation

- New modules and tests may be added when a plan introduces a durable command family or evidence type.
- Module descriptions may be refined as responsibilities move, provided command and evidence ownership remains clear.
- Test surface descriptions may change when behavior moves between focused test modules.

## Drift / Leakage Signals

- CLI and MCP behavior diverge from shared command contracts.
- A write surface bypasses confirmation or atomic JSON/Markdown pair writers.
- A runtime module consumes quality signals before `docs/architecture/quality-signals.md` defines the vocabulary.
- A new seeded owner doc changes in `abh/init.py` without matching current owner-doc guidance.

## Correction Path

- Update this map in the same plan that adds, removes, or reassigns module ownership.
- If a command contract changes, update `abh.commands`, adapters, tests, and this map together.
- If seeded owner docs drift from current owner docs, update `abh/init.py` and the current docs in the same audited slice.
