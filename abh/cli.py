from __future__ import annotations

import argparse
import sys
from typing import Any

from .agent_setup import agent_setup_bundle
from .codex_setup import codex_off, codex_on, codex_status
from .audit_bundle import audit_bundle
from .commands import abh_error_payload, dumps_envelope, make_envelope
from .hooks import hook_profile, install_hooks
from .navigation import onboarding_check, recommend_next_action
from .models import CommitmentPhaseState, CommitmentResidualPressure, MEMORY_STATUSES, REFERENCE_SET_KEYS, empty_reference_set
from .reporting import project_health_report
from .core import (
    AbhError,
    add_memory,
    analyze_drift,
    analyze_plan_drift,
    active_attractor,
    close_plan,
    create_plan,
    create_attractor,
    doctor,
    list_attractors,
    list_audits,
    list_memories,
    list_plans,
    list_roadmap_items,
    load_attractor,
    materialize_roadmap_item,
    next_plan_id,
    next_plan_sequence,
    plan_status_line,
    record_audit,
    record_verification,
    request_audit,
    route_question,
    run_verification,
    search_memory,
    supersede_attractor,
    transition_plan,
    update_plan_record,
    validate_identifier,
)
from .init import run_init


def add_json_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")


def command_name(args: argparse.Namespace) -> str:
    parts = [str(args.command)]
    for attr in (
        "plan_command",
        "verify_command",
        "audit_command",
        "memory_command",
        "drift_command",
        "attractor_command",
        "roadmap_command",
        "agent_command",
        "agent_setup_command",
        "hooks_command",
        "codex_command",
        "onboarding_command",
        "report_command",
    ):
        value = getattr(args, attr, None)
        if value:
            parts.append(str(value))
    return " ".join(parts)


def add_commitment_phase_state_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--stable-state-now", action="append", default=[])
    parser.add_argument("--active-change-pressure", action="append", default=[])
    parser.add_argument("--target-stable-state", action="append", default=[])
    parser.add_argument("--conversion-proof", action="append", default=[])
    parser.add_argument("--residual-pressure", action="append", default=[])


def parse_reference_set_entries(values: list[str]) -> dict[str, list[str]]:
    reference_set = empty_reference_set()
    for raw in values:
        if "=" not in raw:
            raise AbhError("invalid reference set entry; expected KEY=VALUE")
        key, value = raw.split("=", 1)
        key = key.strip()
        value = value.strip()
        if key not in REFERENCE_SET_KEYS:
            raise AbhError(f"invalid reference set key: {key}")
        if not value:
            raise AbhError(f"reference set value must not be empty: {key}")
        if value not in reference_set[key]:
            reference_set[key].append(value)
    return reference_set


def commitment_phase_state_from_args(args: argparse.Namespace) -> CommitmentPhaseState | None:
    stable_state_now = list(getattr(args, "stable_state_now", []) or [])
    active_change_pressure = list(getattr(args, "active_change_pressure", []) or [])
    target_stable_state = list(getattr(args, "target_stable_state", []) or [])
    conversion_proof = list(getattr(args, "conversion_proof", []) or [])
    residual_pressure_args = list(getattr(args, "residual_pressure", []) or [])
    if not any(
        (
            stable_state_now,
            active_change_pressure,
            target_stable_state,
            conversion_proof,
            residual_pressure_args,
        )
    ):
        return None

    residual_pressure: list[CommitmentResidualPressure] = []
    for item in residual_pressure_args:
        pressure, _, rationale = item.partition("|")
        residual_pressure.append(
            CommitmentResidualPressure(
                pressure=pressure.strip(),
                non_blocking_rationale=rationale.strip(),
            )
        )
    return CommitmentPhaseState(
        stable_state_now=stable_state_now,
        active_change_pressure=active_change_pressure,
        target_stable_state=target_stable_state,
        conversion_proof=conversion_proof,
        residual_pressure=residual_pressure,
    )


def print_json_envelope(
    *,
    ok: bool,
    command: str,
    data: dict[str, Any] | None = None,
    errors: list[dict[str, Any]] | None = None,
    warnings: list[dict[str, Any]] | None = None,
) -> None:
    print(dumps_envelope(ok=ok, command=command, data=data, errors=errors, warnings=warnings))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="abh", description="Attractor Before Harness CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="preview or initialize an ABH workspace")
    init_parser.add_argument("--write", action="store_true", help="write the previewed ABH workspace files")
    init_parser.add_argument("--confirm", action="store_true", help="confirm init writes")
    add_json_argument(init_parser)
    init_parser.set_defaults(handler=handle_init)

    agent_parser = subparsers.add_parser("agent", help="export agent setup bundles")
    agent_sub = agent_parser.add_subparsers(dest="agent_command", required=True)

    agent_setup = agent_sub.add_parser("setup", help="export read-only setup bundle")
    agent_setup_sub = agent_setup.add_subparsers(dest="agent_setup_command", required=True)
    for target in ("codex", "claude-code", "mcp"):
        setup_target = agent_setup_sub.add_parser(target, help=f"export {target} setup bundle")
        add_json_argument(setup_target)
        setup_target.set_defaults(handler=handle_agent_setup)

    hooks_parser = subparsers.add_parser("hooks", help="inspect or install local ABH hook guardrails")
    hooks_sub = hooks_parser.add_subparsers(dest="hooks_command", required=True)

    hooks_profile_parser = hooks_sub.add_parser("profile", help="preview the default hook guardrail profile")
    add_json_argument(hooks_profile_parser)
    hooks_profile_parser.set_defaults(handler=handle_hooks_profile)

    hooks_install_parser = hooks_sub.add_parser("install", help="preview or install managed ABH hook guardrails")
    hooks_install_parser.add_argument("--write", action="store_true", help="write the managed hook file")
    hooks_install_parser.add_argument("--confirm", action="store_true", help="confirm hook writes")
    add_json_argument(hooks_install_parser)
    hooks_install_parser.set_defaults(handler=handle_hooks_install)

    codex_parser = subparsers.add_parser("codex", help="manage repository-local Codex ABH guidance")
    codex_sub = codex_parser.add_subparsers(dest="codex_command", required=True)

    codex_status_parser = codex_sub.add_parser("status", help="show Codex ABH status for this repository")
    add_json_argument(codex_status_parser)
    codex_status_parser.set_defaults(handler=handle_codex_status)

    codex_on_parser = codex_sub.add_parser("on", help="preview or write managed Codex ABH config")
    codex_on_parser.add_argument("--write", action="store_true", help="write the managed Codex config")
    codex_on_parser.add_argument("--confirm", action="store_true", help="confirm Codex config writes")
    add_json_argument(codex_on_parser)
    codex_on_parser.set_defaults(handler=handle_codex_on)

    codex_off_parser = codex_sub.add_parser("off", help="preview or remove managed Codex ABH config")
    codex_off_parser.add_argument("--write", action="store_true", help="remove the managed Codex config")
    codex_off_parser.add_argument("--confirm", action="store_true", help="confirm Codex config removal")
    add_json_argument(codex_off_parser)
    codex_off_parser.set_defaults(handler=handle_codex_off)

    next_parser = subparsers.add_parser("next", help="recommend the next ABH action")
    add_json_argument(next_parser)
    next_parser.set_defaults(handler=handle_next)

    onboarding_parser = subparsers.add_parser("onboarding", help="check ABH onboarding readiness")
    onboarding_sub = onboarding_parser.add_subparsers(dest="onboarding_command", required=True)
    onboarding_check_parser = onboarding_sub.add_parser("check", help="check whether this repository is ABH-ready")
    add_json_argument(onboarding_check_parser)
    onboarding_check_parser.set_defaults(handler=handle_onboarding_check)

    plan_parser = subparsers.add_parser("plan", help="manage plans")
    plan_sub = plan_parser.add_subparsers(dest="plan_command", required=True)

    create = plan_sub.add_parser("create", help="create a plan")
    create.add_argument("--id", required=True)
    create.add_argument("--title", required=True)
    create.add_argument("--attractor", help="attractor path; defaults to active attractor")
    create.add_argument("--baseline", help="baseline description; auto-generated if omitted")
    create.add_argument("--owner", default="platform")
    create.add_argument("--status", choices=["draft", "ready"], default="draft")
    create.add_argument("--goal", action="append", default=[])
    create.add_argument("--non-goal", action="append", default=[])
    create.add_argument("--exit-criterion", action="append", default=[])
    create.add_argument("--validation", action="append", default=[])
    create.add_argument("--closure-evidence", action="append", default=[])
    create.add_argument("--scope", action="append", default=[], help="directory scope for structural drift check at close")
    create.add_argument("--reference-set", action="append", default=[], metavar="KEY=VALUE")
    add_commitment_phase_state_arguments(create)
    add_json_argument(create)
    create.set_defaults(handler=handle_plan_create)

    status = plan_sub.add_parser("status", help="show plan status")
    status.add_argument("plan_id")
    add_json_argument(status)
    status.set_defaults(handler=handle_plan_status)

    plan_list = plan_sub.add_parser("list", help="list all plans")
    add_json_argument(plan_list)
    plan_list.set_defaults(handler=handle_plan_list)

    update = plan_sub.add_parser("update", help="append fields to a plan")
    update.add_argument("plan_id")
    update.add_argument("--goal", action="append", default=[])
    update.add_argument("--non-goal", action="append", default=[])
    update.add_argument("--exit-criterion", action="append", default=[])
    update.add_argument("--validation", action="append", default=[])
    update.add_argument("--remove-validation", action="append", default=[])
    update.add_argument("--closure-evidence", action="append", default=[])
    update.add_argument("--scope", action="append", default=[], help="directory scope for structural drift check at close")
    update.add_argument("--reference-set", action="append", default=[], metavar="KEY=VALUE")
    add_commitment_phase_state_arguments(update)
    add_json_argument(update)
    update.set_defaults(handler=handle_plan_update)

    transition = plan_sub.add_parser("transition", help="move plan to another status")
    transition.add_argument("plan_id")
    transition.add_argument("--to", required=True, choices=["draft", "ready", "running", "blocked", "closing", "closed"])
    transition.set_defaults(handler=handle_plan_transition)

    plan_run = plan_sub.add_parser("run", help="compound: transition to running + verify in one step")
    plan_run.add_argument("plan_id")
    add_json_argument(plan_run)
    plan_run.set_defaults(handler=handle_plan_run)

    plan_finish = plan_sub.add_parser("finish", help="pre-close completeness check with auto-fix for git staleness")
    plan_finish.add_argument("plan_id")
    add_json_argument(plan_finish)
    plan_finish.set_defaults(handler=handle_plan_finish)

    verify_parser = subparsers.add_parser("verify", help="record verification runs")
    verify_sub = verify_parser.add_subparsers(dest="verify_command", required=True)

    record = verify_sub.add_parser("record", help="record a verification run")
    record.add_argument("plan_id")
    record.add_argument("--command", required=True)
    record.add_argument("--result", required=True, choices=["pass", "fail", "partial"])
    record.add_argument("--artifact", action="append", default=[])
    record.add_argument("--failed-check", action="append", default=[])
    record.set_defaults(handler=handle_verify_record)

    run = verify_sub.add_parser("run", help="execute plan validation checklist")
    run.add_argument("plan_id")
    run.add_argument("--timeout", type=int, default=120)
    add_json_argument(run)
    run.set_defaults(handler=handle_verify_run)

    audit_parser = subparsers.add_parser("audit", help="manage independent audits")
    audit_sub = audit_parser.add_subparsers(dest="audit_command", required=True)

    audit_request = audit_sub.add_parser("request", help="request an audit")
    audit_request.add_argument("plan_id")
    audit_request.add_argument("--id", required=True)
    audit_request.add_argument("--auditor", required=True)
    audit_request.add_argument("--scope", required=True)
    audit_request.add_argument("--evidence", action="append", default=[])
    audit_request.set_defaults(handler=handle_audit_request)

    audit_record = audit_sub.add_parser("record", help="record an audit verdict")
    audit_record.add_argument("audit_id")
    audit_record.add_argument("--result", required=True, choices=["pass", "fail", "partial", "need_info"])
    audit_record.add_argument("--rationale", required=True)
    audit_record.add_argument("--auditor-context")
    audit_record.add_argument("--independence", choices=["unknown", "independent", "self_review"])
    audit_record.add_argument("--verification-id")
    audit_record.add_argument("--finding", action="append", default=[])
    audit_record.add_argument("--follow-up", action="append", default=[])
    audit_record.add_argument("--from-protocol", help="read verdict from structured JSON file (agent-to-agent protocol)")
    audit_record.set_defaults(handler=handle_audit_record)

    audit_list = audit_sub.add_parser("list", help="list all audits")
    add_json_argument(audit_list)
    audit_list.set_defaults(handler=handle_audit_list)

    audit_bundle_parser = audit_sub.add_parser("bundle", help="generate a read-only audit prompt bundle")
    audit_bundle_parser.add_argument("plan_id")
    audit_bundle_parser.add_argument("--protocol", action="store_true", help="output structured JSON protocol for agent-to-agent audit")
    add_json_argument(audit_bundle_parser)
    audit_bundle_parser.set_defaults(handler=handle_audit_bundle)

    close = subparsers.add_parser("close", help="close a plan after passing audit")
    close.add_argument("plan_id")
    close.set_defaults(handler=handle_close)

    attractor_parser = subparsers.add_parser("attractor", help="manage attractors")
    attractor_sub = attractor_parser.add_subparsers(dest="attractor_command", required=True)

    attractor_list = attractor_sub.add_parser("list", help="list attractors")
    add_json_argument(attractor_list)
    attractor_list.set_defaults(handler=handle_attractor_list)

    attractor_show = attractor_sub.add_parser("show", help="show an attractor")
    attractor_show.add_argument("attractor_id")
    add_json_argument(attractor_show)
    attractor_show.set_defaults(handler=handle_attractor_show)

    attractor_active = attractor_sub.add_parser("active", help="show active attractor")
    add_json_argument(attractor_active)
    attractor_active.set_defaults(handler=handle_attractor_active)

    attractor_create = attractor_sub.add_parser("create", help="create an attractor")
    attractor_create.add_argument("--id", required=True)
    attractor_create.add_argument("--title", required=True)
    attractor_create.add_argument("--version", required=True)
    attractor_create.add_argument("--path", required=True)
    attractor_create.add_argument("--owner", default="architecture")
    attractor_create.add_argument("--intent", required=True)
    attractor_create.add_argument("--invariant", action="append", default=[])
    add_json_argument(attractor_create)
    attractor_create.set_defaults(handler=handle_attractor_create)

    attractor_supersede = attractor_sub.add_parser("supersede", help="supersede an attractor")
    attractor_supersede.add_argument("old_id")
    attractor_supersede.add_argument("--id", required=True)
    attractor_supersede.add_argument("--title", required=True)
    attractor_supersede.add_argument("--version", required=True)
    attractor_supersede.add_argument("--path", required=True)
    attractor_supersede.add_argument("--owner", default="architecture")
    attractor_supersede.add_argument("--intent")
    attractor_supersede.add_argument("--invariant", action="append", default=[])
    attractor_supersede.add_argument("--reason", required=True)
    attractor_supersede.add_argument("--impact", required=True)
    attractor_supersede.add_argument("--migration-strategy", required=True)
    add_json_argument(attractor_supersede)
    attractor_supersede.set_defaults(handler=handle_attractor_supersede)

    roadmap_parser = subparsers.add_parser("roadmap", help="manage roadmap queue")
    roadmap_sub = roadmap_parser.add_subparsers(dest="roadmap_command", required=True)

    roadmap_list = roadmap_sub.add_parser("list", help="list roadmap queue items")
    add_json_argument(roadmap_list)
    roadmap_list.set_defaults(handler=handle_roadmap_list)

    roadmap_next_id = roadmap_sub.add_parser("next-id", help="show next materialized plan id prefix")
    add_json_argument(roadmap_next_id)
    roadmap_next_id.set_defaults(handler=handle_roadmap_next_id)

    roadmap_check = roadmap_sub.add_parser("check", help="check roadmap queue consistency")
    add_json_argument(roadmap_check)
    roadmap_check.set_defaults(handler=handle_roadmap_check)

    roadmap_materialize = roadmap_sub.add_parser("materialize", help="materialize a roadmap item into the next plan id")
    roadmap_materialize.add_argument("key")
    add_json_argument(roadmap_materialize)
    roadmap_materialize.set_defaults(handler=handle_roadmap_materialize)

    report_parser = subparsers.add_parser("report", help="generate ABH reports")
    report_sub = report_parser.add_subparsers(dest="report_command", required=True)

    report_health = report_sub.add_parser("health", help="report project health and semantic pressure")
    add_json_argument(report_health)
    report_health.set_defaults(handler=handle_report_health)

    report_dashboard = report_sub.add_parser("dashboard", help="single-screen project overview for agents and humans")
    add_json_argument(report_dashboard)
    report_dashboard.set_defaults(handler=handle_dashboard)

    doctor_parser = subparsers.add_parser("doctor", help="check workspace consistency")
    doctor_parser.add_argument("--fix", action="store_true", help="auto-migrate outdated schema records to current version")
    add_json_argument(doctor_parser)
    doctor_parser.set_defaults(handler=handle_doctor)

    memory_parser = subparsers.add_parser("memory", help="manage externalized memory")
    memory_sub = memory_parser.add_subparsers(dest="memory_command", required=True)

    memory_add = memory_sub.add_parser("add", help="add a memory record")
    memory_add.add_argument("--id", required=True)
    memory_add.add_argument("--type", required=True, choices=["false_assumption", "rejected_path", "divergent_pattern", "overturned_completion"])
    memory_add.add_argument("--summary", required=True)
    memory_add.add_argument("--context", required=True)
    memory_add.add_argument("--implication", required=True)
    memory_add.add_argument("--evidence", action="append", default=[])
    memory_add.add_argument("--related", action="append", default=[])
    memory_add.add_argument("--tag", action="append", default=[])
    memory_add.add_argument("--status", choices=MEMORY_STATUSES, default="active")
    memory_add.add_argument("--related-plan", action="append", default=[])
    memory_add.add_argument("--related-audit", action="append", default=[])
    memory_add.add_argument("--related-drift", action="append", default=[])
    memory_add.add_argument("--superseded-by", default="")
    memory_add.add_argument("--deprecation-policy")
    memory_add.set_defaults(handler=handle_memory_add)

    memory_search = memory_sub.add_parser("search", help="search memory records")
    memory_search.add_argument("--type", choices=["false_assumption", "rejected_path", "divergent_pattern", "overturned_completion"])
    memory_search.add_argument("--query")
    memory_search.add_argument("--status", choices=MEMORY_STATUSES)
    memory_search.add_argument("--tag")
    memory_search.add_argument("--related-plan")
    memory_search.add_argument("--related-audit")
    memory_search.add_argument("--related-drift")
    add_json_argument(memory_search)
    memory_search.set_defaults(handler=handle_memory_search)

    memory_list = memory_sub.add_parser("list", help="list all memory records")
    add_json_argument(memory_list)
    memory_list.set_defaults(handler=handle_memory_list)

    memory_triage = memory_sub.add_parser("triage", help="list orphaned active memories with triage guidance")
    add_json_argument(memory_triage)
    memory_triage.set_defaults(handler=handle_memory_triage)

    memory_update = memory_sub.add_parser("update", help="update a memory record (append tags, relationships, or change status)")
    memory_update.add_argument("memory_id")
    memory_update.add_argument("--add-tags", action="append", default=[], help="append tags to memory")
    memory_update.add_argument("--add-related-plan", action="append", default=[], dest="add_related_plans", help="append related plan id")
    memory_update.add_argument("--add-related-audit", action="append", default=[], dest="add_related_audits", help="append related audit id")
    memory_update.add_argument("--add-related-drift", action="append", default=[], dest="add_related_drifts", help="append related drift id")
    memory_update.add_argument("--status", choices=MEMORY_STATUSES, help="change memory status")
    add_json_argument(memory_update)
    memory_update.set_defaults(handler=handle_memory_update)

    route = subparsers.add_parser("route", help="recommend reading order for a question")
    route.add_argument("--question", required=True)
    add_json_argument(route)
    route.set_defaults(handler=handle_route)

    drift_parser = subparsers.add_parser("drift", help="analyze drift")
    drift_sub = drift_parser.add_subparsers(dest="drift_command", required=True)

    drift_analyze = drift_sub.add_parser("analyze", help="analyze drift from a text source")
    drift_analyze.add_argument("--id", required=True)
    drift_analyze.add_argument("--source", required=True)
    drift_analyze.add_argument("--evidence", action="append", default=[])
    drift_analyze.add_argument("--memory-id")
    drift_analyze.add_argument("--plan")
    add_json_argument(drift_analyze)
    drift_analyze.set_defaults(handler=handle_drift_analyze)

    drift_plan_check = drift_sub.add_parser("plan-check", help="check plan-bound structural drift against baseline")
    drift_plan_check.add_argument("plan_id", help="plan id to check")
    add_json_argument(drift_plan_check)
    drift_plan_check.set_defaults(handler=handle_drift_plan_check)

    return parser


def handle_init(args: argparse.Namespace) -> int:
    result = run_init(write=args.write, confirmed=args.confirm)
    if args.json:
        print_json_envelope(ok=True, command=command_name(args), data={"init": result})
        return 0
    mode = "wrote" if args.write else "preview"
    print(f"init {mode}: {len(result['writes'])} write(s), {len(result['skips'])} skip(s)")
    return 0


def handle_agent_setup(args: argparse.Namespace) -> int:
    setup = agent_setup_bundle(args.agent_setup_command)
    if args.json:
        print_json_envelope(ok=True, command=command_name(args), data={"setup": setup})
        return 0
    print(f"agent setup {setup['agent']}: read-only bundle")
    return 0


def handle_hooks_profile(args: argparse.Namespace) -> int:
    profile = hook_profile()
    if args.json:
        print_json_envelope(ok=True, command=command_name(args), data={"profile": profile})
        return 0
    print(f"hooks profile {profile['name']}: {profile['path']}")
    return 0


def handle_hooks_install(args: argparse.Namespace) -> int:
    result = install_hooks(write=args.write, confirmed=args.confirm)
    if args.json:
        print_json_envelope(ok=True, command=command_name(args), data={"install": result})
        return 0
    mode = "wrote" if args.write else "preview"
    print(f"hooks install {mode}: {len(result['writes'])} write(s), {len(result['blockers'])} blocker(s)")
    return 0


def handle_codex_status(args: argparse.Namespace) -> int:
    result = codex_status()
    if args.json:
        print_json_envelope(ok=True, command=command_name(args), data={"codex": result})
        return 0
    status = "enabled" if result["enabled"] else "disabled"
    print(f"codex status: {status} ({result['path']})")
    return 0


def handle_codex_on(args: argparse.Namespace) -> int:
    result = codex_on(write=args.write, confirmed=args.confirm)
    if args.json:
        print_json_envelope(ok=True, command=command_name(args), data={"codex": result})
        return 0
    mode = "wrote" if args.write else "preview"
    print(f"codex on {mode}: {len(result['writes'])} write(s), {len(result['blockers'])} blocker(s)")
    return 0


def handle_codex_off(args: argparse.Namespace) -> int:
    result = codex_off(write=args.write, confirmed=args.confirm)
    if args.json:
        print_json_envelope(ok=True, command=command_name(args), data={"codex": result})
        return 0
    mode = "wrote" if args.write else "preview"
    print(f"codex off {mode}: {len(result['writes'])} write(s), {len(result['blockers'])} blocker(s)")
    return 0


def handle_next(args: argparse.Namespace) -> int:
    result = recommend_next_action()
    if args.json:
        print_json_envelope(ok=True, command=command_name(args), data={"next": result})
        return 0
    print(result["recommended_command"])
    return 0


def handle_onboarding_check(args: argparse.Namespace) -> int:
    result = onboarding_check()
    if args.json:
        print_json_envelope(ok=bool(result["ready"]), command=command_name(args), data={"onboarding": result})
        return 0 if result["ready"] else 1
    status = "ready" if result["ready"] else "not ready"
    print(f"onboarding: {status}")
    return 0 if result["ready"] else 1


def handle_plan_create(args: argparse.Namespace) -> int:
    # Smart defaults for agent UX: auto-populate attractor, baseline, validation.
    attractor = args.attractor
    if not attractor:
        from .attractors import active_attractor
        attractor = active_attractor().path
    baseline = args.baseline
    if not baseline:
        import subprocess
        try:
            r = subprocess.run(["git", "log", "--oneline", "-3"], text=True, capture_output=True, timeout=5)
            recent = r.stdout.strip().replace("\n", "; ") if r.returncode == 0 else "baseline"
        except Exception:
            recent = "baseline"
        baseline = f"Auto-generated baseline. Recent commits: {recent}"
    validation = list(args.validation)
    if not validation:
        validation = ["python3 -m pytest tests/ -q", "python3 -m abh doctor", "git diff --check"]
    owner = args.owner
    if owner == "platform":
        import subprocess
        try:
            r = subprocess.run(["git", "config", "user.name"], text=True, capture_output=True, timeout=5)
            if r.returncode == 0 and r.stdout.strip():
                owner = r.stdout.strip()
        except Exception:
            pass

    plan = create_plan(
        plan_id=args.id,
        title=args.title,
        attractor=attractor,
        baseline=baseline,
        owner=owner,
        status=args.status,
        goals=args.goal,
        non_goals=args.non_goal,
        exit_criteria=args.exit_criterion,
        validation_checklist=validation,
        closure_evidence=args.closure_evidence,
        commitment_phase_state=commitment_phase_state_from_args(args),
        scope_paths=args.scope,
        reference_set=parse_reference_set_entries(args.reference_set),
    )
    if args.json:
        print_json_envelope(ok=True, command=command_name(args), data={"plan": plan.to_dict()})
        return 0
    print(f"created plan {args.id}")
    return 0


def handle_plan_status(args: argparse.Namespace) -> int:
    from .core import load_plan
    from .plans import verification_freshness_summary
    from .navigation import _related_memories
    from .memory import load_memory

    validate_identifier(args.plan_id, "plan id")
    plan = load_plan(args.plan_id)
    related_ids = _related_memories(plan)
    related_memories = []
    warnings = []
    for mem_id in related_ids[:5]:
        try:
            mem = load_memory(mem_id)
            related_memories.append({"id": mem.id, "summary": mem.summary, "memory_type": mem.memory_type})
            warnings.append(f"Related memory {mem.id}: {mem.summary[:100]}")
        except Exception:
            pass

    if args.json:
        print_json_envelope(
            ok=True,
            command=command_name(args),
            data={
                "plan": plan.to_dict(),
                "verification_summary": verification_freshness_summary(plan),
                "related_memories": related_memories,
                "warnings": warnings,
            },
        )
        return 0
    print(plan_status_line(plan))
    if warnings:
        print(f"\nRelated memories:")
        for w in warnings:
            print(f"  {w}")
    return 0


def handle_plan_transition(args: argparse.Namespace) -> int:
    transition_plan(args.plan_id, args.to)
    print(f"transitioned {args.plan_id} -> {args.to}")
    return 0


def handle_plan_run(args: argparse.Namespace) -> int:
    """Compound: transition plan to running and run verification in one step."""
    from .plans import load_plan, transition_plan as _transition
    plan = load_plan(args.plan_id)
    steps: list[str] = []

    # Auto-transition through draft→ready→running
    if plan.status == "draft":
        _transition(args.plan_id, "ready")
        steps.append("draft→ready")
        plan = load_plan(args.plan_id)
    if plan.status == "ready":
        _transition(args.plan_id, "running")
        steps.append("ready→running")
        plan = load_plan(args.plan_id)
    if plan.status == "running":
        from .verifications import run_verification
        run = run_verification(plan_id=args.plan_id)
        steps.append(f"verified={run.result}")
    else:
        steps.append(f"status={plan.status} (no verification needed)")

    plan = load_plan(args.plan_id)
    if args.json:
        from .plans import verification_freshness_summary
        print_json_envelope(
            ok=plan.status == "running",
            command=command_name(args),
            data={"plan": plan.to_dict(), "steps": steps, "verification_summary": verification_freshness_summary(plan)},
        )
        return 0 if plan.status == "running" else 1
    print(f"plan run {args.plan_id}: {' → '.join(steps)}")
    return 0 if plan.status == "running" else 1


def handle_plan_finish(args: argparse.Namespace) -> int:
    """Pre-close completeness check with auto-fix for git staleness."""
    from .plans import load_plan, verification_freshness_summary, audit_close_blocker, _auto_reverify_if_git_only
    from .audits import load_audit

    plan = load_plan(args.plan_id)
    issues: list[str] = []
    ok_checks: list[str] = []

    if not plan.closure_evidence:
        issues.append("no closure evidence")
    else:
        ok_checks.append("closure evidence present")

    if not plan.audit_ids:
        issues.append("no audit — request one with: abh audit request <plan-id> ...")
    else:
        for audit_id in plan.audit_ids:
            audit = load_audit(audit_id)
            if audit.result == "pass" and audit.status == "complete":
                reason = audit_close_blocker(plan, audit)
                if reason:
                    if "stale" in reason:
                        plan, new_reason = _auto_reverify_if_git_only(plan, audit, audit_id)
                        if new_reason is None:
                            ok_checks.append(f"audit {audit_id} pass (auto-reverified)")
                            break
                        if new_reason != "__skipped__":
                            reason = new_reason
                    issues.append(f"audit {audit_id}: {reason}")
                else:
                    ok_checks.append(f"audit {audit_id} pass")
                    break
            else:
                issues.append(f"audit {audit_id}: result={audit.result}, status={audit.status}")

    if args.json:
        ready = not issues
        print_json_envelope(
            ok=ready,
            command=command_name(args),
            data={
                "plan_id": args.plan_id,
                "ready_to_close": ready,
                "issues": issues,
                "ok_checks": ok_checks,
                "next_action": "abh close " + args.plan_id if ready else "fix issues above then re-run abh plan finish " + args.plan_id,
            },
        )
        return 0 if ready else 1

    print(f"plan finish {args.plan_id}:")
    for check in ok_checks:
        print(f"  ✓ {check}")
    for issue in issues:
        print(f"  ✗ {issue}")
    if not issues:
        print(f"\nReady to close. Run: abh close {args.plan_id}")
    else:
        print(f"\n{len(issues)} blocker(s) to resolve before close.")
    return 0 if not issues else 1


def handle_plan_update(args: argparse.Namespace) -> int:
    plan = update_plan_record(
        plan_id=args.plan_id,
        goals=args.goal,
        non_goals=args.non_goal,
        exit_criteria=args.exit_criterion,
        validation_checklist=args.validation,
        remove_validation_checklist=args.remove_validation,
        closure_evidence=args.closure_evidence,
        commitment_phase_state=commitment_phase_state_from_args(args),
        scope=args.scope,
        reference_set=parse_reference_set_entries(args.reference_set),
    )
    if args.json:
        print_json_envelope(ok=True, command=command_name(args), data={"plan": plan.to_dict()})
        return 0
    print(f"updated plan {plan.id}")
    return 0


def handle_plan_list(args: argparse.Namespace) -> int:
    plans = list_plans()
    if args.json:
        print_json_envelope(
            ok=True,
            command=command_name(args),
            data={"plans": [plan.to_dict() for plan in plans], "total": len(plans)},
        )
        return 0
    for plan in plans:
        runs = len(plan.verification_runs)
        audits = len(plan.audit_ids)
        print(f"{plan.id}  [{plan.status}]  {plan.title}  (verifications: {runs}, audits: {audits})")
    print(f"\ntotal: {len(plans)} plan(s)")
    return 0


def handle_verify_record(args: argparse.Namespace) -> int:
    run = record_verification(
        plan_id=args.plan_id,
        command=args.command,
        result=args.result,
        artifacts=args.artifact,
        failed_checks=args.failed_check,
    )
    print(f"recorded verification {run.id} for {args.plan_id}")
    return 0


def handle_verify_run(args: argparse.Namespace) -> int:
    run = run_verification(plan_id=args.plan_id, timeout_seconds=args.timeout)
    if args.json:
        print_json_envelope(
            ok=run.result == "pass",
            command=command_name(args),
            data={"verification": run.to_dict()},
            errors=[] if run.result == "pass" else [
                {
                    "code": "verification_failed",
                    "message": "one or more validation checks failed",
                    "category": "business_rule",
                    "details": {"failed_checks": run.failed_checks},
                }
            ],
        )
        return 0 if run.result == "pass" else 1
    print(f"ran verification {run.id} for {args.plan_id}: {run.result}")
    return 0 if run.result == "pass" else 1


def handle_audit_request(args: argparse.Namespace) -> int:
    audit = request_audit(
        audit_id=args.id,
        plan_id=args.plan_id,
        auditor=args.auditor,
        scope=args.scope,
        evidence=args.evidence,
    )
    print(f"requested audit {audit.id} for {audit.plan_id}")
    return 0


def handle_audit_record(args: argparse.Namespace) -> int:
    result = args.result
    rationale = args.rationale
    findings = args.finding
    follow_ups = args.follow_up

    if args.from_protocol:
        import json as _json
        with open(args.from_protocol, "r", encoding="utf-8") as f:
            protocol = _json.load(f)
        result = protocol.get("result", result)
        rationale = protocol.get("rationale", rationale)
        findings = protocol.get("findings", [])
        if isinstance(findings, list) and findings and isinstance(findings[0], dict):
            findings = [f"{f.get('severity','')}|{f.get('title','')}|{f.get('evidence','')}|{f.get('recommendation','')}" for f in findings]
        follow_ups = protocol.get("follow_ups", follow_ups)
        if args.independence is None:
            args.independence = protocol.get("independence")

    audit = record_audit(
        audit_id=args.audit_id,
        result=result,
        rationale=rationale,
        auditor_context=args.auditor_context,
        independence=args.independence,
        verification_id=args.verification_id,
        findings=findings,
        follow_ups=follow_ups,
    )
    print(f"recorded audit {audit.id}: {audit.result}")
    return 0


def handle_audit_list(args: argparse.Namespace) -> int:
    audits = list_audits()
    if args.json:
        print_json_envelope(
            ok=True,
            command=command_name(args),
            data={"audits": [audit.to_dict() for audit in audits], "total": len(audits)},
        )
        return 0
    for audit in audits:
        status_info = f" [{audit.status}]" if audit.status == "complete" else ""
        result_info = f" result={audit.result}" if audit.status == "complete" else ""
        print(f"{audit.id}  -> {audit.plan_id}{status_info}{result_info}")
    print(f"\ntotal: {len(audits)} audit(s)")
    return 0


def handle_audit_bundle(args: argparse.Namespace) -> int:
    bundle = audit_bundle(args.plan_id)
    if args.protocol:
        protocol = {
            "protocol_version": "1",
            "plan_id": bundle["plan"]["id"],
            "plan_title": bundle["plan"]["title"],
            "goals": bundle["plan"]["goals"],
            "non_goals": bundle["plan"]["non_goals"],
            "exit_criteria": bundle["plan"]["exit_criteria"],
            "verification_id": bundle["latest_verification"].get("latest_id"),
            "evidence_paths": [
                p for v in bundle["evidence"].values()
                for p in (v if isinstance(v, list) else [v]) if p
            ],
            "expected_response": {
                "result": "pass|fail|partial|need_info",
                "rationale": "<concise explanation>",
                "independence": "independent|self_review|unknown",
                "findings": [
                    {"severity": "low|medium|high", "title": "...", "evidence": "...", "recommendation": "..."}
                ],
                "follow_ups": ["<action item>"],
            },
            "instructions": "Read the evidence paths. Check goals against code, non-goals against implementation, exit criteria against verification. Return a JSON object matching expected_response. Do NOT modify files. Return ONLY the JSON object.",
        }
        if args.json:
            print_json_envelope(ok=True, command=command_name(args), data={"audit_protocol": protocol})
            return 0
        import json as _json
        print(_json.dumps(protocol, indent=2))
        return 0
    if args.json:
        print_json_envelope(ok=True, command=command_name(args), data={"audit_bundle": bundle})
        return 0
    print(bundle["prompt"])
    return 0


def handle_close(args: argparse.Namespace) -> int:
    plan = close_plan(args.plan_id)
    print(f"closed plan {plan.id}")
    return 0


def handle_attractor_list(args: argparse.Namespace) -> int:
    attractors = list_attractors()
    if args.json:
        print_json_envelope(
            ok=True,
            command=command_name(args),
            data={"attractors": [attractor.to_dict() for attractor in attractors], "total": len(attractors)},
        )
        return 0
    for attractor in attractors:
        print(f"{attractor.id}  [{attractor.status}]  {attractor.title}  ({attractor.version})")
    print(f"\ntotal: {len(attractors)} attractor(s)")
    return 0


def handle_attractor_show(args: argparse.Namespace) -> int:
    attractor = load_attractor(args.attractor_id)
    if args.json:
        print_json_envelope(ok=True, command=command_name(args), data={"attractor": attractor.to_dict()})
        return 0
    print(f"{attractor.id} [{attractor.status}]")
    print(f"title: {attractor.title}")
    print(f"version: {attractor.version}")
    print(f"path: {attractor.path}")
    return 0


def handle_attractor_active(args: argparse.Namespace) -> int:
    attractor = active_attractor()
    if args.json:
        print_json_envelope(ok=True, command=command_name(args), data={"attractor": attractor.to_dict()})
        return 0
    print(f"{attractor.id} [{attractor.status}] {attractor.path}")
    return 0


def handle_attractor_create(args: argparse.Namespace) -> int:
    attractor = create_attractor(
        attractor_id=args.id,
        title=args.title,
        version=args.version,
        path=args.path,
        owner=args.owner,
        intent=args.intent,
        invariants=args.invariant,
    )
    if args.json:
        print_json_envelope(ok=True, command=command_name(args), data={"attractor": attractor.to_dict()})
        return 0
    print(f"created attractor {attractor.id}")
    return 0


def handle_attractor_supersede(args: argparse.Namespace) -> int:
    old, attractor = supersede_attractor(
        old_id=args.old_id,
        new_id=args.id,
        title=args.title,
        version=args.version,
        path=args.path,
        owner=args.owner,
        intent=args.intent,
        invariants=args.invariant or None,
        reason=args.reason,
        impact=args.impact,
        migration_strategy=args.migration_strategy,
    )
    if args.json:
        print_json_envelope(
            ok=True,
            command=command_name(args),
            data={"old_attractor": old.to_dict(), "attractor": attractor.to_dict()},
        )
        return 0
    print(f"superseded {old.id} -> {attractor.id}")
    return 0


def handle_roadmap_list(args: argparse.Namespace) -> int:
    items = list_roadmap_items()
    if args.json:
        print_json_envelope(
            ok=True,
            command=command_name(args),
            data={"items": [item.to_dict() for item in items], "total": len(items)},
        )
        return 0
    for item in items:
        plan_info = f" -> {item.plan_id}" if item.plan_id else ""
        print(f"{item.key} [{item.status}]{plan_info} {item.title}")
    print(f"\ntotal: {len(items)} roadmap item(s)")
    return 0


def handle_roadmap_next_id(args: argparse.Namespace) -> int:
    sequence = next_plan_sequence()
    plan_id = next_plan_id()
    if args.json:
        print_json_envelope(
            ok=True,
            command=command_name(args),
            data={"next_plan_id": plan_id, "next_sequence": sequence},
        )
        return 0
    print(plan_id)
    return 0


def handle_roadmap_check(args: argparse.Namespace) -> int:
    from .core import check_plan_numbering, check_roadmap_queue

    issues = check_plan_numbering() + check_roadmap_queue()
    if args.json:
        print_json_envelope(ok=not issues, command=command_name(args), data={"issues": issues})
        return 0 if not issues else 1
    if not issues:
        print("roadmap: ok")
        return 0
    print("roadmap: found consistency issues")
    for issue in issues:
        print(f"- {issue}")
    return 1


def handle_roadmap_materialize(args: argparse.Namespace) -> int:
    item, plan = materialize_roadmap_item(args.key)
    if args.json:
        print_json_envelope(
            ok=True,
            command=command_name(args),
            data={"item": item.to_dict(), "plan": plan.to_dict()},
        )
        return 0
    print(f"materialized {item.key} -> {plan.id}")
    return 0


def handle_report_health(args: argparse.Namespace) -> int:
    report = project_health_report()
    if args.json:
        print_json_envelope(ok=True, command=command_name(args), data={"health_report": report})
        return 0
    print(f"health: {report['posture']}")
    print(report["summary"])
    return 0


def handle_dashboard(args: argparse.Namespace) -> int:
    """Single-screen project overview: health + plans + roadmap + memories."""
    from .reporting import project_health_report
    from .plans import list_plans
    from .roadmap import list_roadmap_items
    from .memory import triage_memories

    health = project_health_report()
    plans = list_plans()
    roadmap = list_roadmap_items()
    orphaned = triage_memories()

    recent_plans = sorted(
        [p for p in plans if p.status == "closed"],
        key=lambda p: p.updated_at, reverse=True,
    )[:5]
    queued = [i for i in roadmap if i.status == "queued"]
    high_signals = [s for s in health.get("semantic_pressure", []) if s.get("severity") == "high"]

    if args.json:
        print_json_envelope(ok=True, command=command_name(args), data={
            "posture": health["posture"],
            "summary": health["summary"],
            "metrics": health.get("metrics", {}),
            "recent_plans": [{"id": p.id, "title": p.title, "status": p.status, "updated_at": p.updated_at} for p in recent_plans],
            "queued_roadmap": [{"key": i.key, "title": i.title, "stage": i.stage} for i in queued],
            "orphaned_memories": orphaned,
            "high_signals_count": len(high_signals),
            "top_signals": [{"type": s["type"], "severity": s["severity"], "summary": s["summary"]} for s in high_signals[:5]],
            "recommended_action": _dashboard_recommendation(health, queued, orphaned),
        })
        return 0

    print(f" ABH Dashboard")
    print(f" ─────────────────────────────────────────")
    print(f" Posture: {health['posture']}     Plans: {len(plans)}     Memory: {health['metrics']['memory']['total']}")
    print(f" Roadmap: {len(queued)} queued  Audits: {health['metrics']['audit']['total']} ({health['metrics']['audit']['pass']} pass)")
    print(f" ─────────────────────────────────────────")
    if queued:
        print(f" Queued Roadmap:")
        for i in queued[:5]:
            print(f"  ▸ {i.key}  [{i.stage}]  {i.title[:60]}")
    print(f" ─────────────────────────────────────────")
    if recent_plans:
        print(f" Recent Activity:")
        for p in recent_plans[:5]:
            print(f"  {p.id}  [{p.status}]  {p.title[:50]}")
    print(f" ─────────────────────────────────────────")
    print(f" Top Signals:")
    if high_signals:
        for s in high_signals[:3]:
            print(f"  ⚠ [{s['severity']}] {s['summary'][:80]}")
    else:
        print(f"  ✓ No high-severity signals")
    if orphaned:
        print(f"  ⚡ {len(orphaned)} orphaned memories → abh memory triage")
    rec = _dashboard_recommendation(health, queued, orphaned)
    if rec:
        print(f" ─────────────────────────────────────────")
        print(f" Next: {rec}")
    return 0


def _dashboard_recommendation(health: dict, queued: list, orphaned: list) -> str | None:
    if queued:
        return f"materialize next roadmap item: abh roadmap materialize {queued[0].key}"
    if orphaned:
        return f"triage orphaned memories: abh memory triage"
    return None


def handle_doctor(args: argparse.Namespace) -> int:
    issues = doctor(fix=args.fix)
    if args.json:
        if not issues:
            print_json_envelope(ok=True, command=command_name(args), data={"issues": []})
            return 0
        print_json_envelope(
            ok=False,
            command=command_name(args),
            data={"issues": issues},
            errors=[
                {
                    "code": "doctor_issues",
                    "message": "doctor found consistency issues",
                    "category": "consistency",
                    "details": {"issues": issues},
                }
            ],
        )
        return 1
    if not issues:
        label = "doctor: ok"
        if args.fix:
            label = "doctor: ok (migrations applied if needed)"
        print(label)
        return 0
    label = "doctor: found consistency issues"
    if args.fix:
        label = "doctor: found consistency issues (migrations applied)"
    print(label)
    for issue in issues:
        print(f"- {issue}")
    return 1


def handle_memory_add(args: argparse.Namespace) -> int:
    memory = add_memory(
        memory_id=args.id,
        memory_type=args.type,
        summary=args.summary,
        context=args.context,
        implication=args.implication,
        evidence=args.evidence,
        related=args.related,
        tags=args.tag,
        status=args.status,
        related_plan_ids=args.related_plan,
        related_audit_ids=args.related_audit,
        related_drift_ids=args.related_drift,
        superseded_by=args.superseded_by,
        deprecation_policy=args.deprecation_policy,
    )
    print(f"recorded memory {memory.id}")
    return 0


def handle_memory_search(args: argparse.Namespace) -> int:
    results = search_memory(
        memory_type=args.type,
        query=args.query,
        status=args.status,
        tag=args.tag,
        related_plan_id=args.related_plan,
        related_audit_id=args.related_audit,
        related_drift_id=args.related_drift,
    )
    if args.json:
        print_json_envelope(
            ok=True,
            command=command_name(args),
            data={"memories": [memory.to_dict() for memory in results], "total": len(results)},
        )
        return 0
    for memory in results:
        print(f"{memory.id} [{memory.memory_type}] {memory.summary}")
    return 0


def handle_memory_list(args: argparse.Namespace) -> int:
    memories = list_memories()
    if args.json:
        print_json_envelope(
            ok=True,
            command=command_name(args),
            data={"memories": [memory.to_dict() for memory in memories], "total": len(memories)},
        )
        return 0
    for mem in memories:
        evidence_count = len(mem.evidence)
        print(f"{mem.id}  [{mem.memory_type}]  {mem.summary}  (evidence: {evidence_count})")
    print(f"\ntotal: {len(memories)} memory record(s)")
    return 0


def handle_memory_triage(args: argparse.Namespace) -> int:
    from .memory import triage_memories

    orphaned = triage_memories()
    if args.json:
        print_json_envelope(
            ok=True,
            command=command_name(args),
            data={"memories": orphaned, "total": len(orphaned)},
        )
        return 0
    if not orphaned:
        print("no orphaned active memories found")
        return 0
    print(f"{len(orphaned)} orphaned active memor(y|ies):\n")
    for mem in orphaned:
        flags = []
        if not mem["has_tags"]:
            flags.append("no tags")
        if not mem["has_relations"]:
            flags.append("no relations")
        print(f"  {mem['id']}  [{mem['memory_type']}]  ({', '.join(flags)})")
        print(f"    summary: {mem['summary'][:100]}")
        if not mem["has_tags"]:
            print(f"    action:  abh memory update {mem['id']} --add-tags <tag>")
        if not mem["has_relations"]:
            print(f"    action:  abh memory update {mem['id']} --add-related-plan <plan-id>")
        print()
    return 0


def handle_memory_update(args: argparse.Namespace) -> int:
    from .memory import update_memory

    memory = update_memory(
        memory_id=args.memory_id,
        add_tags=args.add_tags or None,
        add_related_plan_ids=args.add_related_plans or None,
        add_related_audit_ids=args.add_related_audits or None,
        add_related_drift_ids=args.add_related_drifts or None,
        status=args.status,
    )
    if args.json:
        print_json_envelope(ok=True, command=command_name(args), data={"memory": memory.to_dict()})
        return 0
    print(f"updated memory {memory.id}: tags={memory.tags}, related_plans={memory.related_plan_ids}")
    return 0


def handle_route(args: argparse.Namespace) -> int:
    result = route_question(args.question)
    if args.json:
        print_json_envelope(ok=True, command=command_name(args), data={"route": result})
        return 0
    print(f"Route: {result['route']}")
    print("Reading order:")
    for item in result["reading_order"]:
        print(f"- {item}")
    print(f"Rationale: {result['rationale']}")
    return 0


def handle_drift_analyze(args: argparse.Namespace) -> int:
    report = analyze_drift(
        drift_id=args.id,
        source=args.source,
        evidence=args.evidence,
        memory_id=args.memory_id,
        plan_id=args.plan,
    )
    if args.json:
        print_json_envelope(ok=True, command=command_name(args), data={"drift_report": report.to_dict()})
        return 0
    print(f"drift report {report.id}")
    for finding in report.findings:
        print(f"- {finding.drift_type}: {finding.evidence}")
    return 0


def handle_drift_plan_check(args: argparse.Namespace) -> int:
    from .boundary import check_plan_scope

    findings = analyze_plan_drift(plan_id=args.plan_id)
    scope_findings = check_plan_scope(plan_id=args.plan_id)
    findings = list(findings) + list(scope_findings)
    if args.json:
        print_json_envelope(
            ok=True, command=command_name(args),
            data={"findings": [f.to_dict() for f in findings], "total": len(findings)},
        )
        return 0
    if not findings:
        print(f"plan-check {args.plan_id}: ok (no non-goal violations in import changes)")
        return 0
    print(f"plan-check {args.plan_id}: {len(findings)} non-goal violation(s)")
    for f in findings:
        print(f"- [{f.severity}] {f.evidence}")
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
        handler = getattr(args, "handler", None)
        if handler is None:
            parser.print_help()
            return 1
        return handler(args)
    except AbhError as exc:
        if "args" in locals() and getattr(args, "json", False):
            print_json_envelope(ok=False, command=command_name(args), errors=[abh_error_payload(exc)])
            return 2
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except SystemExit as exc:
        return int(exc.code)
