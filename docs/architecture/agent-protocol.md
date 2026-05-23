# ABH Agent Protocol

## Purpose

Agent Protocol is the programmatic interface that lets AI agents read and later write ABH governance state without scraping human-oriented CLI text.

The protocol does not replace the CLI. The CLI remains the execution substrate; Agent Protocol defines the structured contracts that can be exposed through JSON output and MCP tools.

## Current Gap

ABH currently has a parameterized CLI for plans, verifications, audits, memory, routing, drift, close, and doctor. Its outputs are primarily natural text produced with `print()`.

That means an agent can run commands, but cannot reliably parse results, distinguish business blocking from system errors, or discover stable tool schemas.

## Principles

- Repository files remain the source of truth.
- Human-readable Markdown and natural CLI output remain supported by default.
- Machine-readable output must be explicit, stable, and schema-versioned.
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

The first MCP Server should be read-only.

Allowed tools:

- read plan status
- list plans
- list audits
- list/search memory
- route a question
- run doctor

Deferred tools:

- create plan
- transition plan
- record verification
- request or record audit
- close plan
- add memory
- analyze and write drift reports

### Layer 5: Controlled Write MCP Tools

Write tools may be added only after JSON output and read-only MCP are stable.

Write tools must:

- call the same core functions as the CLI
- preserve state transition rules
- preserve audit-before-close
- preserve doctor and schema expectations
- return structured verification evidence
- be covered by CLI and MCP contract tests

## Near-term Plans

- `plan-012-agent-protocol-foundation`: define this protocol baseline and align roadmap/task-board.
- `plan-013-json-output-and-errors`: implement JSON output and structured errors for read commands.
- `plan-014-readonly-mcp-server`: expose read-only MCP tools over the JSON/internal object contract.

## Non-goals

- Do not implement MCP before JSON contracts are clear.
- Do not make JSON output the default human CLI output.
- Do not give agents write tools before read tools are stable.
- Do not bypass ABH closure, audit, memory, or doctor gates.
