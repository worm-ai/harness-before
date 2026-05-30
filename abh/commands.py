from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from .models import SCHEMA_VERSION


@dataclass(frozen=True, slots=True)
class CommandContract:
    id: str
    cli_command: str
    mcp_tool: str | None
    read_only: bool
    confirmation: str
    side_effects: list[str]
    description: str
    input_schema: dict[str, Any]
    output_keys: list[str]
    failure_categories: list[str]


def text_property(description: str) -> dict[str, str]:
    return {"type": "string", "description": description}


def bool_property(description: str) -> dict[str, str]:
    return {"type": "boolean", "description": description}


def array_property(description: str) -> dict[str, Any]:
    return {"type": "array", "description": description, "items": {"type": "string"}}


def input_schema(properties: dict[str, Any], required: list[str] | None = None) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": properties,
        "required": list(required or []),
        "additionalProperties": False,
    }


def make_envelope(
    *,
    ok: bool,
    command: str,
    data: dict[str, Any] | None = None,
    errors: list[dict[str, Any]] | None = None,
    warnings: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "ok": ok,
        "command": command,
        "data": data or {},
        "errors": errors or [],
        "warnings": warnings or [],
    }


def dumps_envelope(
    *,
    ok: bool,
    command: str,
    data: dict[str, Any] | None = None,
    errors: list[dict[str, Any]] | None = None,
    warnings: list[dict[str, Any]] | None = None,
) -> str:
    return json.dumps(
        make_envelope(ok=ok, command=command, data=data, errors=errors, warnings=warnings),
        ensure_ascii=False,
    )


COMMON_FAILURES = ["validation", "not_found", "business_rule", "consistency", "system"]


COMMANDS: tuple[CommandContract, ...] = (
    CommandContract(
        id="init.workspace",
        cli_command="init",
        mcp_tool=None,
        read_only=False,
        confirmation="--write --confirm",
        side_effects=[
            "create .abh/ workspace directories",
            "create docs/index.md",
            "create docs/context/ owner docs",
            "create docs/requirements/ and docs/design/ directories",
            "write .abh/attractors/attractor-abh-core.json",
            "write docs/architecture/attractors/abh-core-attractor.md when absent",
        ],
        description="Preview or initialize an ABH workspace around the default active attractor and AGE owner docs.",
        input_schema=input_schema(
            {
                "write": bool_property("Write the previewed workspace files."),
                "confirm": bool_property("Must be present with --write to permit repository writes."),
            }
        ),
        output_keys=["init"],
        failure_categories=COMMON_FAILURES,
    ),
    CommandContract(
        id="agent.setup.codex",
        cli_command="agent setup codex",
        mcp_tool=None,
        read_only=True,
        confirmation="none",
        side_effects=[],
        description="Export a read-only Codex setup bundle from the active attractor and Agent-First contract.",
        input_schema=input_schema({}),
        output_keys=["setup"],
        failure_categories=["not_found", "consistency", "system"],
    ),
    CommandContract(
        id="agent.setup.claude_code",
        cli_command="agent setup claude-code",
        mcp_tool=None,
        read_only=True,
        confirmation="none",
        side_effects=[],
        description="Export a read-only Claude Code setup bundle from the active attractor and Agent-First contract.",
        input_schema=input_schema({}),
        output_keys=["setup"],
        failure_categories=["not_found", "consistency", "system"],
    ),
    CommandContract(
        id="agent.setup.mcp",
        cli_command="agent setup mcp",
        mcp_tool=None,
        read_only=True,
        confirmation="none",
        side_effects=[],
        description="Export a read-only generic MCP setup bundle including the ABH MCP server command.",
        input_schema=input_schema({}),
        output_keys=["setup"],
        failure_categories=["not_found", "consistency", "system"],
    ),
    CommandContract(
        id="hooks.profile",
        cli_command="hooks profile",
        mcp_tool=None,
        read_only=True,
        confirmation="none",
        side_effects=[],
        description="Preview the default local ABH hook guardrail profile without modifying repository state.",
        input_schema=input_schema({}),
        output_keys=["profile"],
        failure_categories=["system"],
    ),
    CommandContract(
        id="hooks.install",
        cli_command="hooks install",
        mcp_tool=None,
        read_only=False,
        confirmation="--write --confirm",
        side_effects=["write .git/hooks/pre-commit"],
        description="Install or refresh the managed local ABH pre-commit guardrail hook.",
        input_schema=input_schema(
            {
                "write": bool_property("Write the managed hook file."),
                "confirm": bool_property("Must be present with --write to permit repository writes."),
            }
        ),
        output_keys=["install"],
        failure_categories=COMMON_FAILURES,
    ),
    CommandContract(
        id="next",
        cli_command="next",
        mcp_tool=None,
        read_only=True,
        confirmation="none",
        side_effects=[],
        description="Recommend the next safe ABH action from local repository state.",
        input_schema=input_schema({}),
        output_keys=["next"],
        failure_categories=["consistency", "system"],
    ),
    CommandContract(
        id="onboarding.check",
        cli_command="onboarding check",
        mcp_tool=None,
        read_only=True,
        confirmation="none",
        side_effects=[],
        description="Check whether this repository is ABH-ready for agent workflows.",
        input_schema=input_schema({}),
        output_keys=["onboarding"],
        failure_categories=["consistency", "system"],
    ),
    CommandContract(
        id="attractor.list",
        cli_command="attractor list",
        mcp_tool="abh_attractor_list",
        read_only=True,
        confirmation="none",
        side_effects=[],
        description="List ABH attractor records without modifying repository state.",
        input_schema=input_schema({}),
        output_keys=["attractors", "total"],
        failure_categories=["system"],
    ),
    CommandContract(
        id="attractor.show",
        cli_command="attractor show",
        mcp_tool="abh_attractor_show",
        read_only=True,
        confirmation="none",
        side_effects=[],
        description="Read one ABH attractor by id.",
        input_schema=input_schema({"attractor_id": text_property("Attractor id.")}, ["attractor_id"]),
        output_keys=["attractor"],
        failure_categories=["validation", "not_found", "system"],
    ),
    CommandContract(
        id="attractor.active",
        cli_command="attractor active",
        mcp_tool="abh_attractor_active",
        read_only=True,
        confirmation="none",
        side_effects=[],
        description="Read the current active ABH attractor.",
        input_schema=input_schema({}),
        output_keys=["attractor"],
        failure_categories=["not_found", "consistency", "system"],
    ),
    CommandContract(
        id="attractor.create",
        cli_command="attractor create",
        mcp_tool=None,
        read_only=False,
        confirmation="cli write command",
        side_effects=["write .abh/attractors/<attractor_id>.json", "write docs/architecture/attractors/<name>.md", "mark existing active attractor inactive"],
        description="Create an ABH attractor and make it active.",
        input_schema=input_schema(
            {
                "attractor_id": text_property("Attractor id."),
                "title": text_property("Attractor title."),
                "version": text_property("Attractor version."),
                "path": text_property("Attractor Markdown path."),
                "owner": text_property("Owner label."),
                "intent": text_property("Attractor intent."),
                "invariants": array_property("Attractor invariants."),
            },
            ["attractor_id", "title", "version", "path", "intent"],
        ),
        output_keys=["attractor"],
        failure_categories=COMMON_FAILURES,
    ),
    CommandContract(
        id="attractor.supersede",
        cli_command="attractor supersede",
        mcp_tool=None,
        read_only=False,
        confirmation="cli write command",
        side_effects=["mark old attractor inactive", "write new active attractor JSON and Markdown"],
        description="Create a new active attractor that supersedes an existing attractor.",
        input_schema=input_schema(
            {
                "old_id": text_property("Superseded attractor id."),
                "attractor_id": text_property("New attractor id."),
                "title": text_property("New attractor title."),
                "version": text_property("New attractor version."),
                "path": text_property("New attractor Markdown path."),
                "owner": text_property("Owner label."),
                "intent": text_property("Optional replacement intent."),
                "invariants": array_property("Optional replacement invariants."),
                "reason": text_property("Supersession reason."),
                "impact": text_property("Impact scope."),
                "migration_strategy": text_property("Migration strategy."),
            },
            ["old_id", "attractor_id", "title", "version", "path", "reason", "impact", "migration_strategy"],
        ),
        output_keys=["old_attractor", "attractor"],
        failure_categories=COMMON_FAILURES,
    ),
    CommandContract(
        id="plan.list",
        cli_command="plan list",
        mcp_tool="abh_plan_list",
        read_only=True,
        confirmation="none",
        side_effects=[],
        description="List ABH plans without modifying repository state.",
        input_schema=input_schema({}),
        output_keys=["plans", "total"],
        failure_categories=["system"],
    ),
    CommandContract(
        id="plan.status",
        cli_command="plan status",
        mcp_tool="abh_plan_status",
        read_only=True,
        confirmation="none",
        side_effects=[],
        description="Read one ABH plan by id.",
        input_schema=input_schema({"plan_id": text_property("Plan id, for example plan-014-readonly-mcp-server.")}, ["plan_id"]),
        output_keys=["plan", "verification_summary"],
        failure_categories=["validation", "not_found", "system"],
    ),
    CommandContract(
        id="plan.create",
        cli_command="plan create",
        mcp_tool="abh_plan_create",
        read_only=False,
        confirmation="confirm=true",
        side_effects=["write .abh/plans/<plan_id>.json", "write docs/plans/<plan_id>.md"],
        description="Create an ABH plan through existing core rules.",
        input_schema=input_schema(
            {
                "confirm": bool_property("Must be true to permit repository writes."),
                "plan_id": text_property("Plan id to create."),
                "title": text_property("Plan title."),
                "attractor": text_property("Attractor document path."),
                "baseline": text_property("Baseline document path or baseline label."),
                "owner": text_property("Optional owner."),
                "status": text_property("draft or ready."),
                "goals": array_property("Plan goals."),
                "non_goals": array_property("Plan non-goals."),
                "exit_criteria": array_property("Plan exit criteria."),
                "validation_checklist": array_property("Validation checklist."),
                "closure_evidence": array_property("Closure evidence paths."),
            },
            ["confirm", "plan_id", "title", "attractor", "baseline"],
        ),
        output_keys=["plan"],
        failure_categories=COMMON_FAILURES,
    ),
    CommandContract(
        id="plan.update",
        cli_command="plan update",
        mcp_tool=None,
        read_only=False,
        confirmation="cli write command",
        side_effects=["update .abh/plans/<plan_id>.json", "update docs/plans/<plan_id>.md"],
        description="Append or remove supported plan fields through existing core rules.",
        input_schema=input_schema({"plan_id": text_property("Plan id.")}, ["plan_id"]),
        output_keys=["plan"],
        failure_categories=COMMON_FAILURES,
    ),
    CommandContract(
        id="roadmap.list",
        cli_command="roadmap list",
        mcp_tool="abh_roadmap_list",
        read_only=True,
        confirmation="none",
        side_effects=[],
        description="List stable roadmap queue items without assigning plan numbers.",
        input_schema=input_schema({}),
        output_keys=["items", "total"],
        failure_categories=["system"],
    ),
    CommandContract(
        id="roadmap.next_id",
        cli_command="roadmap next-id",
        mcp_tool="abh_roadmap_next_id",
        read_only=True,
        confirmation="none",
        side_effects=[],
        description="Compute the next materialized plan id prefix from existing plans.",
        input_schema=input_schema({}),
        output_keys=["next_plan_id", "next_sequence"],
        failure_categories=["system"],
    ),
    CommandContract(
        id="roadmap.check",
        cli_command="roadmap check",
        mcp_tool="abh_roadmap_check",
        read_only=True,
        confirmation="none",
        side_effects=[],
        description="Check roadmap queue and plan-numbering consistency.",
        input_schema=input_schema({}),
        output_keys=["issues"],
        failure_categories=["consistency", "system"],
    ),
    CommandContract(
        id="roadmap.materialize",
        cli_command="roadmap materialize",
        mcp_tool=None,
        read_only=False,
        confirmation="cli write command",
        side_effects=["write .abh/plans/<plan_id>.json", "write docs/plans/<plan_id>.md", "update .abh/roadmap.json item plan_id"],
        description="Materialize a roadmap queue item into the next available concrete plan id.",
        input_schema=input_schema({"key": text_property("Stable roadmap item key.")}, ["key"]),
        output_keys=["item", "plan"],
        failure_categories=COMMON_FAILURES,
    ),
    CommandContract(
        id="plan.transition",
        cli_command="plan transition",
        mcp_tool="abh_plan_transition",
        read_only=False,
        confirmation="confirm=true",
        side_effects=["update .abh/plans/<plan_id>.json", "update docs/plans/<plan_id>.md"],
        description="Transition an ABH plan through the existing state machine.",
        input_schema=input_schema(
            {
                "confirm": bool_property("Must be true to permit repository writes."),
                "plan_id": text_property("Plan id."),
                "to": text_property("Target status."),
            },
            ["confirm", "plan_id", "to"],
        ),
        output_keys=["plan"],
        failure_categories=COMMON_FAILURES,
    ),
    CommandContract(
        id="verification.record",
        cli_command="verify record",
        mcp_tool="abh_verify_record",
        read_only=False,
        confirmation="confirm=true",
        side_effects=["write .abh/verifications/<verification_id>.json", "update associated plan record"],
        description="Record verification evidence for a plan.",
        input_schema=input_schema(
            {
                "confirm": bool_property("Must be true to permit repository writes."),
                "plan_id": text_property("Plan id."),
                "command": text_property("Verification command."),
                "result": text_property("pass, fail, or partial."),
                "artifacts": array_property("Verification artifact paths."),
                "failed_checks": array_property("Failed checks."),
            },
            ["confirm", "plan_id", "command", "result"],
        ),
        output_keys=["verification"],
        failure_categories=COMMON_FAILURES,
    ),
    CommandContract(
        id="verification.run",
        cli_command="verify run",
        mcp_tool=None,
        read_only=False,
        confirmation="cli execution command",
        side_effects=["execute validation checklist in local shell", "write verification record", "update associated plan record"],
        description="Execute a plan validation checklist and record verification evidence.",
        input_schema=input_schema({"plan_id": text_property("Plan id."), "timeout": text_property("Timeout seconds.")}, ["plan_id"]),
        output_keys=["verification"],
        failure_categories=["validation", "business_rule", "system"],
    ),
    CommandContract(
        id="audit.list",
        cli_command="audit list",
        mcp_tool="abh_audit_list",
        read_only=True,
        confirmation="none",
        side_effects=[],
        description="List ABH audit records without modifying repository state.",
        input_schema=input_schema({}),
        output_keys=["audits", "total"],
        failure_categories=["system"],
    ),
    CommandContract(
        id="audit.bundle",
        cli_command="audit bundle",
        mcp_tool=None,
        read_only=True,
        confirmation="none",
        side_effects=[],
        description="Generate a read-only independent audit prompt and evidence bundle for a plan.",
        input_schema=input_schema({"plan_id": text_property("Plan id to audit.")}, ["plan_id"]),
        output_keys=["audit_bundle"],
        failure_categories=["validation", "not_found", "system"],
    ),
    CommandContract(
        id="audit.request",
        cli_command="audit request",
        mcp_tool="abh_audit_request",
        read_only=False,
        confirmation="confirm=true",
        side_effects=["write .abh/audits/<audit_id>.json", "write docs/audits/<audit_id>.md", "update associated plan record"],
        description="Request an independent audit.",
        input_schema=input_schema(
            {
                "confirm": bool_property("Must be true to permit repository writes."),
                "plan_id": text_property("Plan id."),
                "audit_id": text_property("Audit id."),
                "auditor": text_property("Auditor label."),
                "scope": text_property("Audit scope."),
                "evidence": array_property("Evidence items."),
            },
            ["confirm", "plan_id", "audit_id", "auditor", "scope", "evidence"],
        ),
        output_keys=["audit"],
        failure_categories=COMMON_FAILURES,
    ),
    CommandContract(
        id="audit.record",
        cli_command="audit record",
        mcp_tool="abh_audit_record",
        read_only=False,
        confirmation="confirm=true",
        side_effects=["update .abh/audits/<audit_id>.json", "update docs/audits/<audit_id>.md"],
        description="Record an audit verdict.",
        input_schema=input_schema(
            {
                "confirm": bool_property("Must be true to permit repository writes."),
                "audit_id": text_property("Audit id."),
                "result": text_property("pass, fail, partial, or need_info."),
                "rationale": text_property("Audit rationale."),
                "auditor_context": text_property("Reviewer execution context or source, e.g. isolated session and model/tool."),
                "independence": text_property("unknown, independent, or self_review."),
                "verification_id": text_property("Verification id the audit verdict reviewed."),
                "findings": array_property("Findings in Severity|Finding|Evidence|Recommendation form."),
                "follow_ups": array_property("Follow-up items."),
            },
            ["confirm", "audit_id", "result", "rationale"],
        ),
        output_keys=["audit"],
        failure_categories=COMMON_FAILURES,
    ),
    CommandContract(
        id="plan.close",
        cli_command="close",
        mcp_tool="abh_close_plan",
        read_only=False,
        confirmation="confirm=true",
        side_effects=["update .abh/plans/<plan_id>.json", "update docs/plans/<plan_id>.md"],
        description="Close a plan after a passing audit.",
        input_schema=input_schema(
            {
                "confirm": bool_property("Must be true to permit repository writes."),
                "plan_id": text_property("Plan id."),
            },
            ["confirm", "plan_id"],
        ),
        output_keys=["plan"],
        failure_categories=COMMON_FAILURES,
    ),
    CommandContract(
        id="memory.list",
        cli_command="memory list",
        mcp_tool="abh_memory_list",
        read_only=True,
        confirmation="none",
        side_effects=[],
        description="List ABH memory records without modifying repository state.",
        input_schema=input_schema({}),
        output_keys=["memories", "total"],
        failure_categories=["system"],
    ),
    CommandContract(
        id="memory.search",
        cli_command="memory search",
        mcp_tool="abh_memory_search",
        read_only=True,
        confirmation="none",
        side_effects=[],
        description="Search ABH memory records by optional type and query text.",
        input_schema=input_schema(
            {
                "type": text_property("Optional memory type."),
                "query": text_property("Optional case-insensitive search text."),
                "status": text_property("Optional memory status."),
                "tag": text_property("Optional tag filter."),
                "related_plan_id": text_property("Optional related plan id filter."),
                "related_audit_id": text_property("Optional related audit id filter."),
                "related_drift_id": text_property("Optional related drift report id filter."),
            }
        ),
        output_keys=["memories", "total"],
        failure_categories=["validation", "system"],
    ),
    CommandContract(
        id="memory.add",
        cli_command="memory add",
        mcp_tool="abh_memory_add",
        read_only=False,
        confirmation="confirm=true",
        side_effects=["write .abh/memory/<memory_id>.json", "write docs/memory/<memory_id>.md"],
        description="Add a memory record.",
        input_schema=input_schema(
            {
                "confirm": bool_property("Must be true to permit repository writes."),
                "memory_id": text_property("Memory id."),
                "type": text_property("Memory type."),
                "summary": text_property("Memory summary."),
                "context": text_property("Memory context."),
                "implication": text_property("Memory implication."),
                "evidence": array_property("Evidence items."),
                "related": array_property("Related records."),
                "tags": array_property("Memory tags."),
                "status": text_property("Memory quality-signal status."),
                "related_plan_ids": array_property("Related plan ids."),
                "related_audit_ids": array_property("Related audit ids."),
                "related_drift_ids": array_property("Related drift report ids."),
                "superseded_by": text_property("Replacement memory id when this memory is superseded."),
                "deprecation_policy": text_property("Optional deprecation policy."),
            },
            ["confirm", "memory_id", "type", "summary", "context", "implication", "evidence"],
        ),
        output_keys=["memory"],
        failure_categories=COMMON_FAILURES,
    ),
    CommandContract(
        id="route",
        cli_command="route",
        mcp_tool="abh_route",
        read_only=True,
        confirmation="none",
        side_effects=[],
        description="Recommend ABH reading order for a question.",
        input_schema=input_schema({"question": text_property("Question to route through ABH governance context.")}, ["question"]),
        output_keys=["route"],
        failure_categories=["validation", "system"],
    ),
    CommandContract(
        id="doctor",
        cli_command="doctor",
        mcp_tool="abh_doctor",
        read_only=True,
        confirmation="none",
        side_effects=[],
        description="Check ABH workspace consistency without modifying repository state.",
        input_schema=input_schema({}),
        output_keys=["issues"],
        failure_categories=["consistency", "system"],
    ),
    CommandContract(
        id="drift.list",
        cli_command="drift list",
        mcp_tool="abh_drift_list",
        read_only=True,
        confirmation="none",
        side_effects=[],
        description="List existing ABH drift reports without creating new drift reports.",
        input_schema=input_schema({}),
        output_keys=["drift_reports", "total"],
        failure_categories=["system"],
    ),
    CommandContract(
        id="drift.analyze",
        cli_command="drift analyze",
        mcp_tool="abh_drift_analyze",
        read_only=False,
        confirmation="confirm=true",
        side_effects=["write .abh/drift/<drift_id>.json", "write docs/drift/<drift_id>.md", "optionally write memory record"],
        description="Analyze drift and write a drift report.",
        input_schema=input_schema(
            {
                "confirm": bool_property("Must be true to permit repository writes."),
                "drift_id": text_property("Drift report id."),
                "source": text_property("Text source path to analyze."),
                "evidence": array_property("Evidence items."),
                "memory_id": text_property("Optional memory id to write."),
                "plan_id": text_property("Optional plan id baseline."),
            },
            ["confirm", "drift_id", "source"],
        ),
        output_keys=["drift_report"],
        failure_categories=COMMON_FAILURES,
    ),
)


CONTRACTS_BY_ID = {contract.id: contract for contract in COMMANDS}
CONTRACTS_BY_MCP_TOOL = {contract.mcp_tool: contract for contract in COMMANDS if contract.mcp_tool}


def command_contract(command_id: str) -> CommandContract:
    return CONTRACTS_BY_ID[command_id]


def mcp_tool_contract(tool_name: str) -> CommandContract:
    return CONTRACTS_BY_MCP_TOOL[tool_name]


def mcp_tool_names() -> list[str]:
    return list(CONTRACTS_BY_MCP_TOOL)


def mcp_tool_definition(contract: CommandContract) -> dict[str, Any]:
    return {
        "name": contract.mcp_tool,
        "title": str(contract.mcp_tool).replace("_", " "),
        "description": contract.description,
        "inputSchema": contract.input_schema,
        "annotations": {
            "readOnlyHint": contract.read_only,
            "destructiveHint": not contract.read_only,
            "idempotentHint": contract.read_only,
            "openWorldHint": False,
        },
    }


def mcp_tool_definitions() -> list[dict[str, Any]]:
    return [mcp_tool_definition(contract) for contract in COMMANDS if contract.mcp_tool]
