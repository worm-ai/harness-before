# ABH Agent Protocol

## Purpose

Agent Protocol is the programmatic interface that lets AI agents read and later write ABH governance state without scraping human-oriented CLI text.

The protocol does not replace the CLI. The CLI remains the execution substrate; Agent Protocol defines the structured contracts that can be exposed through JSON output and MCP tools.

## Stage 4 Agent-First Update

Stage 2 made ABH machine-readable. Stage 4 makes ABH agent-first.

Agent-first does not mean humans disappear from the workflow. It means ABH commands are designed primarily as a control plane for Codex, Claude Code, MCP clients, and future agents. Humans define or approve the high-risk boundaries: active attractor changes, repository writes, hook installation, independent audit, and release decisions.

The core Stage 4 interface is an Agent-First Command Contract:

- every agent-facing command has a stable command id;
- every agent-facing command has a JSON envelope;
- every write command declares side effects;
- every write command supports a confirmation boundary such as `confirm=true`, `--confirm`, `--write`, or `--dry-run`;
- CLI, MCP tools, hooks, and future agent setup commands adapt the same contract instead of each defining independent schemas;
- `abh next --json` becomes the default navigation entry for agents deciding which ABH action should happen next.

This updates the Stage 2 principle "machine-readable output must be explicit" into a stronger Stage 4 requirement: machine-readable behavior must be the primary contract for agent-facing automation, while human-readable text remains a compatibility and inspection layer.

## Current Gap

ABH has a parameterized CLI for plans, verifications, audits, memory, routing, drift, close, and doctor. It now exposes explicit JSON output for core read commands, structured ABH errors, and an MCP stdio server.

Before Stage 2, an agent could run commands but could not reliably parse results, distinguish business blocking from system errors, or discover stable tool schemas. Stage 2 closes that gap by making the CLI and MCP contracts machine-readable while keeping repository files as the source of truth.

## Principles

- Repository files remain the source of truth.
- Human-readable Markdown and natural CLI output remain supported by default.
- Machine-readable output must be explicit, stable, and schema-versioned.
- Agent-facing behavior must be non-interactive, repeatable, and safe to call from Codex, Claude Code, and MCP clients.
- CLI and MCP must adapt one shared command contract instead of duplicating schemas and confirmation rules.
- Write operations must expose an explicit approval boundary and must be able to explain their side effects before writing.
- MCP tools must wrap existing ABH behavior instead of bypassing state, audit, or doctor gates.
- Read capability comes before write capability.
- Write capability must preserve existing plan, verification, audit, close, memory, and drift rules.

## Protocol Layers

### Layer 1: JSON CLI Contract

Core read commands should expose a machine-readable mode such as `--json`.

Minimum read commands:

- `abh plan status`
- `abh plan list`
- `abh audit list`
- `abh memory list`
- `abh memory search`
- `abh route`
- `abh doctor`
- `abh drift analyze`

Each JSON response should include:

- `schema_version`
- `ok`
- `command`
- `data`
- `errors`
- `warnings`

Example shape:

```json
{
  "schema_version": "1",
  "ok": true,
  "command": "plan list",
  "data": {
    "plans": []
  },
  "errors": [],
  "warnings": []
}
```

### Layer 2: Structured Error Contract

Agents need structured errors, not stderr text alone.

Error entries should include:

- `code`
- `message`
- `category`
- `details`

Recommended categories:

- `usage`
- `validation`
- `not_found`
- `business_rule`
- `consistency`
- `system`

Exit codes should remain compatible with the current CLI:

- `0`: success
- `1`: consistency or doctor failure
- `2`: ABH validation or business rule error
- parser usage errors continue to follow argparse behavior

### Layer 3: Agent Tool Schema

Agent-facing tools should be derived from CLI commands and internal models.

Initial tool groups:

- `plans`: list plans, show plan status
- `audits`: list audits
- `memory`: list and search memory
- `route`: recommend reading order for a question
- `drift`: analyze text evidence
- `doctor`: report workspace consistency

Each tool must define:

- input schema
- output schema
- side effects
- required evidence
- failure modes

### Layer 4: Read-only MCP Server

The first MCP Server was delivered as read-only before any write tools were opened.

Allowed tools:

- `abh_plan_list`
- `abh_plan_status`
- `abh_audit_list`
- `abh_memory_list`
- `abh_memory_search`
- `abh_route`
- `abh_doctor`
- `abh_drift_list`

Current entrypoint:

```bash
python3 -m abh.mcp_server
```

The server uses stdio JSON-RPC messages and returns MCP tool results with both text content and `structuredContent`. `abh_drift_list` lists existing drift reports without creating new ones.

### Layer 5: Controlled Write MCP Tools

Write tools were added only after JSON output and read-only MCP were stable.

Allowed controlled write tools:

- `abh_plan_create`
- `abh_plan_transition`
- `abh_verify_record`
- `abh_audit_request`
- `abh_audit_record`
- `abh_close_plan`
- `abh_memory_add`
- `abh_drift_analyze`

Write tools must:

- call the same core functions as the CLI
- preserve state transition rules
- preserve audit-before-close
- preserve doctor and schema expectations
- require explicit `confirm=true`
- return structured verification evidence
- be covered by CLI and MCP contract tests

### Layer 6: Agent-First Command Contract

Stage 4 introduces a shared command contract module that both CLI and MCP adapters consume. `plan-028-agent-first-command-contract` started with the existing agent-facing command surface before adding new Stage 4 commands.

Each command contract should describe:

- command id, for example `plan.status` or `agent.setup.codex`;
- input fields and validation rules;
- output payload schema;
- whether the command is read-only or write-capable;
- required confirmation boundary for writes;
- side effects, including files and ABH objects that may be written;
- failure categories and business-rule gates;
- recommended next actions where applicable.

Initial Stage 4 command families:

- `attractor.*`: manage active attractor metadata and supersession records;
- `init.*`: initialize a repository around an active attractor;
- `agent.setup.*`: export setup bundles for Codex, Claude Code, and generic MCP clients;
- `hooks.*`: install or inspect local guardrail hooks;
- `next`: recommend the next ABH action from current repository state;
- `onboarding.check`: check whether the repository is ABH-ready for agents.

The first implementation surface is `abh.commands`. It records stable command ids, CLI command labels, MCP tool names, read/write classification, confirmation boundary, side effects, input schemas, output keys, and failure categories. CLI JSON envelope helpers and MCP tool definitions should consume this layer instead of maintaining parallel schema tables.

The CLI adapter may still provide human-readable output, but every Stage 4 command should first define its JSON result. The MCP adapter should use the same command contract and only translate it into MCP tool metadata and `structuredContent`. Future `abh attractor`, `abh init`, `abh agent setup`, hooks, `abh next`, and onboarding commands must be added to the contract before or alongside their CLI/MCP adapters.

### Layer 7: Agent Navigation

`abh route` answers "what should I read?".

`abh next --json` should answer "what should the agent do next?".

The `next` result should include:

- `next_action`;
- recommended `command`;
- whether the action requires human confirmation;
- rationale grounded in active attractor, plan status, latest verification, audit state, stale summary, and memory where relevant;
- optional alternatives when more than one safe next action exists.

This is the main convenience layer for agents. Agents should not have to memorize ABH workflow order; they should ask ABH for the next valid step.

## Near-term Plans

- `plan-012-agent-protocol-foundation`: completed; defined this protocol baseline and aligned roadmap/task-board.
- `plan-013-json-output-and-errors`: completed; implemented JSON output and structured errors for read commands.
- `plan-014-readonly-mcp-server`: completed; exposes read-only MCP tools over the JSON/internal object contract.
- `plan-015-controlled-mcp-write-tools`: completed; exposes controlled MCP write tools with explicit confirmation and existing ABH gates.
- `plan-027-stage-4-attractor-entry-plan`: completed; defined Agent-First attractor entry and promoted the shared command contract as the technical baseline for `abh attractor`, `abh init`, `abh agent setup`, hooks, `abh next`, and onboarding checks.
- `plan-028-agent-first-command-contract`: completed; extracted the shared command contract layer for the existing CLI/MCP surface and aligned MCP `abh_plan_status` with CLI `plan status --json`.
- `plan-029-attractor-registry`: completed; added the active attractor registry through the shared command contract, CLI commands, MCP read tools, and ready-plan active attractor validation.
- `plan-030-abh-init-active-attractor`: next Stage 4 implementation slice; should bind repository initialization to the current active attractor and seed the baseline `.abh/` layout.

## Milestone Status

Stage 2 / Agent Protocol Foundation is complete as of `plan-015-controlled-mcp-write-tools` closure. ABH has explicit JSON CLI contracts, structured errors, read-only MCP tools, and controlled MCP write tools guarded by explicit confirmation and existing ABH gates.

## Non-goals

- Do not implement MCP before JSON contracts are clear.
- Do not make JSON output the default human CLI output.
- Do not give agents write tools before read tools are stable.
- Do not bypass ABH closure, audit, memory, or doctor gates.
- Do not let Stage 4 setup helpers become human-only wizards; they must produce machine-readable setup bundles first.
