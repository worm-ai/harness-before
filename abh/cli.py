from __future__ import annotations

import argparse
import sys
from typing import Any

from .agent_setup import agent_setup_bundle
from .audit_bundle import audit_bundle
from .commands import dumps_envelope, make_envelope
from .hooks import hook_profile, install_hooks
from .navigation import onboarding_check, recommend_next_action
from .models import MEMORY_STATUSES
from .core import (
    AbhError,
    add_memory,
    analyze_drift,
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
        "onboarding_command",
    ):
        value = getattr(args, attr, None)
        if value:
            parts.append(str(value))
    return " ".join(parts)


def print_json_envelope(
    *,
    ok: bool,
    command: str,
    data: dict[str, Any] | None = None,
    errors: list[dict[str, Any]] | None = None,
    warnings: list[dict[str, Any]] | None = None,
) -> None:
    print(dumps_envelope(ok=ok, command=command, data=data, errors=errors, warnings=warnings))


def categorize_abh_error(message: str) -> str:
    if "not found" in message:
        return "not_found"
    if message.startswith("invalid ") or "missing:" in message or "required" in message:
        return "validation"
    if message.startswith("cannot ") or "transition" in message:
        return "business_rule"
    return "system"


def abh_error_payload(exc: AbhError) -> dict[str, Any]:
    message = str(exc)
    return {
        "code": "abh_error",
        "message": message,
        "category": categorize_abh_error(message),
        "details": {},
    }


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
    create.add_argument("--attractor", required=True)
    create.add_argument("--baseline", required=True)
    create.add_argument("--owner", default="platform")
    create.add_argument("--status", choices=["draft", "ready"], default="draft")
    create.add_argument("--goal", action="append", default=[])
    create.add_argument("--non-goal", action="append", default=[])
    create.add_argument("--exit-criterion", action="append", default=[])
    create.add_argument("--validation", action="append", default=[])
    create.add_argument("--closure-evidence", action="append", default=[])
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
    add_json_argument(update)
    update.set_defaults(handler=handle_plan_update)

    transition = plan_sub.add_parser("transition", help="move plan to another status")
    transition.add_argument("plan_id")
    transition.add_argument("--to", required=True, choices=["draft", "ready", "running", "blocked", "closing", "closed"])
    transition.set_defaults(handler=handle_plan_transition)

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
    audit_record.set_defaults(handler=handle_audit_record)

    audit_list = audit_sub.add_parser("list", help="list all audits")
    add_json_argument(audit_list)
    audit_list.set_defaults(handler=handle_audit_list)

    audit_bundle_parser = audit_sub.add_parser("bundle", help="generate a read-only audit prompt bundle")
    audit_bundle_parser.add_argument("plan_id")
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

    doctor_parser = subparsers.add_parser("doctor", help="check workspace consistency")
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
    create_plan(
        plan_id=args.id,
        title=args.title,
        attractor=args.attractor,
        baseline=args.baseline,
        owner=args.owner,
        status=args.status,
        goals=args.goal,
        non_goals=args.non_goal,
        exit_criteria=args.exit_criterion,
        validation_checklist=args.validation,
        closure_evidence=args.closure_evidence,
    )
    print(f"created plan {args.id}")
    return 0


def handle_plan_status(args: argparse.Namespace) -> int:
    from .core import load_plan
    from .plans import verification_freshness_summary

    validate_identifier(args.plan_id, "plan id")
    plan = load_plan(args.plan_id)
    if args.json:
        print_json_envelope(
            ok=True,
            command=command_name(args),
            data={
                "plan": plan.to_dict(),
                "verification_summary": verification_freshness_summary(plan),
            },
        )
        return 0
    print(plan_status_line(plan))
    return 0


def handle_plan_transition(args: argparse.Namespace) -> int:
    transition_plan(args.plan_id, args.to)
    print(f"transitioned {args.plan_id} -> {args.to}")
    return 0


def handle_plan_update(args: argparse.Namespace) -> int:
    plan = update_plan_record(
        plan_id=args.plan_id,
        goals=args.goal,
        non_goals=args.non_goal,
        exit_criteria=args.exit_criterion,
        validation_checklist=args.validation,
        remove_validation_checklist=args.remove_validation,
        closure_evidence=args.closure_evidence,
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
    audit = record_audit(
        audit_id=args.audit_id,
        result=args.result,
        rationale=args.rationale,
        auditor_context=args.auditor_context,
        independence=args.independence,
        verification_id=args.verification_id,
        findings=args.finding,
        follow_ups=args.follow_up,
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


def handle_doctor(args: argparse.Namespace) -> int:
    issues = doctor()
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
        print("doctor: ok")
        return 0
    print("doctor: found consistency issues")
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
