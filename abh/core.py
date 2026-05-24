from __future__ import annotations

import re
import shlex
import subprocess
import time
import uuid
from collections.abc import Callable
from pathlib import Path

from .models import (
    AUDIT_RESULTS,
    DRIFT_TYPES,
    MEMORY_TYPES,
    PLAN_STATUSES,
    VERIFICATION_RESULTS,
    AuditFinding,
    AuditRecord,
    DriftFinding,
    DriftReport,
    MemoryRecord,
    PlanRecord,
    VerificationRun,
    utc_now,
)
from .storage import (
    audit_doc_path,
    audit_json_path,
    audits_dir,
    drift_dir,
    drift_doc_path,
    drift_json_path,
    docs_audits_dir,
    docs_drift_dir,
    docs_memory_dir,
    docs_plans_dir,
    ensure_workspace,
    memory_doc_path,
    memory_json_path,
    memory_dir,
    plan_doc_path,
    plan_json_path,
    plans_dir,
    read_json,
    verification_path,
    verifications_dir,
    write_json,
)

ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "draft": {"ready"},
    "ready": {"running", "blocked"},
    "running": {"blocked", "closing"},
    "blocked": {"running", "closing"},
    "closing": {"closed"},
    "closed": set(),
}


class AbhError(RuntimeError):
    pass


# Verification runs are JSON-only execution evidence today, so doctor excludes
# them from JSON/Markdown consistency checks until they get a document model.
DOCTOR_OBJECTS: tuple[tuple[str, str, Callable[[Path | None], Path], Callable[[Path | None], Path]], ...] = (
    ("plan", "plan-", plans_dir, docs_plans_dir),
    ("audit", "audit-", audits_dir, docs_audits_dir),
    ("memory", "mem-", memory_dir, docs_memory_dir),
    ("drift", "drift-", drift_dir, docs_drift_dir),
)


def validate_identifier(value: str, label: str = "identifier") -> None:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", value):
        raise AbhError(f"invalid {label}: {value!r}")


def doctor(cwd: Path | None = None) -> list[str]:
    issues: list[str] = []
    for label, prefix, json_dir_factory, docs_dir_factory in DOCTOR_OBJECTS:
        json_dir = json_dir_factory(cwd)
        docs_dir = docs_dir_factory(cwd)
        json_ids = {path.stem for path in json_dir.glob("*.json")} if json_dir.exists() else set()
        if json_dir.exists():
            for path in sorted(json_dir.glob("*.json")):
                data = read_json(path)
                if data.get("schema_version") != "1":
                    issues.append(f"missing schema_version for {label} {path.stem}")
        doc_ids = set()
        if docs_dir.exists():
            doc_ids = {
                path.stem
                for path in docs_dir.glob("*.md")
                if path.name != "README.md" and path.stem.startswith(prefix)
            }
        for object_id in sorted(json_ids - doc_ids):
            issues.append(f"missing markdown for {label} {object_id}")
        for object_id in sorted(doc_ids - json_ids):
            issues.append(f"orphan markdown for {label} {object_id}")
    return issues


def list_plans(cwd: Path | None = None) -> list[PlanRecord]:
    directory = plans_dir(cwd)
    if not directory.exists():
        return []
    plans: list[PlanRecord] = []
    for path in sorted(directory.glob("*.json")):
        plans.append(PlanRecord.from_dict(read_json(path)))
    return plans


def require_existing_path(path_text: str, label: str) -> None:
    path = Path(path_text)
    if not path.exists():
        raise AbhError(f"{label} not found: {path_text}")


def load_plan(plan_id: str, cwd: Path | None = None) -> PlanRecord:
    validate_identifier(plan_id, "plan id")
    path = plan_json_path(plan_id, cwd)
    if not path.exists():
        raise AbhError(f"plan not found: {plan_id}")
    return PlanRecord.from_dict(read_json(path))


def save_plan(plan: PlanRecord, cwd: Path | None = None, write_doc: bool = True) -> PlanRecord:
    ensure_workspace(cwd)
    plan.updated_at = utc_now()
    if write_doc:
        doc_path = plan.doc_path or str(plan_doc_path(plan.id, cwd))
        plan.doc_path = doc_path
        doc = render_plan_markdown(plan)
        doc_file = Path(doc_path)
        doc_file.parent.mkdir(parents=True, exist_ok=True)
        doc_file.write_text(doc, encoding="utf-8")
    write_json(plan_json_path(plan.id, cwd), plan.to_dict())
    return plan


def create_plan(
    *,
    plan_id: str,
    title: str,
    attractor: str,
    baseline: str,
    owner: str = "platform",
    status: str = "draft",
    goals: list[str] | None = None,
    non_goals: list[str] | None = None,
    exit_criteria: list[str] | None = None,
    validation_checklist: list[str] | None = None,
    closure_evidence: list[str] | None = None,
    cwd: Path | None = None,
) -> PlanRecord:
    ensure_workspace(cwd)
    validate_identifier(plan_id, "plan id")
    require_existing_path(attractor, "attractor")
    if status not in {"draft", "ready"}:
        raise AbhError("plan create only supports draft or ready status")
    plan_path = plan_json_path(plan_id, cwd)
    if plan_path.exists():
        raise AbhError(f"plan already exists: {plan_id}")
    plan = PlanRecord(
        id=plan_id,
        title=title,
        attractor=attractor,
        baseline=baseline,
        owner=owner,
        status=status,
        goals=list(goals or []),
        non_goals=list(non_goals or []),
        exit_criteria=list(exit_criteria or []),
        validation_checklist=list(validation_checklist or []),
        closure_evidence=list(closure_evidence or []),
        doc_path=str(plan_doc_path(plan_id, cwd)),
    )
    if status == "ready":
        validate_plan_ready(plan)
    return save_plan(plan, cwd=cwd, write_doc=True)


def append_unique(existing: list[str], additions: list[str] | None) -> list[str]:
    values = list(existing)
    for item in additions or []:
        if item not in values:
            values.append(item)
    return values


def update_plan_record(
    *,
    plan_id: str,
    goals: list[str] | None = None,
    non_goals: list[str] | None = None,
    exit_criteria: list[str] | None = None,
    validation_checklist: list[str] | None = None,
    remove_validation_checklist: list[str] | None = None,
    closure_evidence: list[str] | None = None,
    cwd: Path | None = None,
) -> PlanRecord:
    plan = load_plan(plan_id, cwd)
    if not any((goals, non_goals, exit_criteria, validation_checklist, remove_validation_checklist, closure_evidence)):
        raise AbhError("plan update requires at least one field to append")
    plan.goals = append_unique(plan.goals, goals)
    plan.non_goals = append_unique(plan.non_goals, non_goals)
    plan.exit_criteria = append_unique(plan.exit_criteria, exit_criteria)
    plan.validation_checklist = append_unique(plan.validation_checklist, validation_checklist)
    for item in remove_validation_checklist or []:
        plan.validation_checklist = [value for value in plan.validation_checklist if value != item]
    plan.closure_evidence = append_unique(plan.closure_evidence, closure_evidence)
    return save_plan(plan, cwd=cwd, write_doc=True)


def validate_plan_ready(plan: PlanRecord) -> None:
    missing: list[str] = []
    if not plan.title.strip():
        missing.append("title")
    if not plan.attractor.strip():
        missing.append("attractor")
    if not plan.baseline.strip():
        missing.append("baseline")
    if not plan.goals:
        missing.append("goals")
    if not plan.non_goals:
        missing.append("non_goals")
    if not plan.exit_criteria:
        missing.append("exit_criteria")
    if not plan.validation_checklist:
        missing.append("validation_checklist")
    if not plan.closure_evidence:
        missing.append("closure_evidence")
    if missing:
        raise AbhError(f"plan is not ready; missing: {', '.join(missing)}")


def transition_plan(plan_id: str, target_status: str, cwd: Path | None = None) -> PlanRecord:
    if target_status not in PLAN_STATUSES:
        raise AbhError(f"invalid target status: {target_status}")
    plan = load_plan(plan_id, cwd)
    allowed = ALLOWED_TRANSITIONS[plan.status]
    if target_status not in allowed:
        raise AbhError(f"invalid transition: {plan.status} -> {target_status}")
    if target_status == "ready":
        validate_plan_ready(plan)
    if target_status == "closing":
        if not plan.verification_runs:
            raise AbhError("cannot move to closing without verification runs")
        latest = load_verification(plan.verification_runs[-1], cwd)
        if latest.result != "pass":
            raise AbhError("cannot move to closing without a passing verification run")
    plan.status = target_status
    return save_plan(plan, cwd)


def load_verification(run_id: str, cwd: Path | None = None) -> VerificationRun:
    path = verification_path(run_id, cwd)
    if not path.exists():
        raise AbhError(f"verification run not found: {run_id}")
    return VerificationRun.from_dict(read_json(path))


def record_verification(
    *,
    plan_id: str,
    command: str,
    result: str,
    artifacts: list[str] | None = None,
    failed_checks: list[str] | None = None,
    cwd: Path | None = None,
) -> VerificationRun:
    if result not in VERIFICATION_RESULTS:
        raise AbhError(f"invalid verification result: {result}")
    if not command.strip():
        raise AbhError("verification command is required")
    plan = load_plan(plan_id, cwd)
    ensure_workspace(cwd)
    run = VerificationRun(
        id=f"ver-{uuid.uuid4().hex[:12]}",
        plan_id=plan_id,
        command=command,
        result=result,
        artifacts=list(artifacts or []),
        failed_checks=list(failed_checks or []),
    )
    write_json(verification_path(run.id, cwd), run.to_dict())
    plan.verification_runs.append(run.id)
    if result in {"fail", "partial"} and plan.status in {"ready", "running"}:
        plan.status = "blocked"
    save_plan(plan, cwd)
    return run


def is_recursive_verify_command(command: str, plan_id: str) -> bool:
    try:
        parts = shlex.split(command)
    except ValueError:
        return False
    if len(parts) < 5:
        return False
    for index in range(len(parts) - 4):
        if parts[index:index + 4] == ["python3", "-m", "abh", "verify"] and "run" in parts[index + 4:]:
            return plan_id in parts[index + 4:]
        if parts[index:index + 4] == ["python", "-m", "abh", "verify"] and "run" in parts[index + 4:]:
            return plan_id in parts[index + 4:]
    return False


def run_verification(
    *,
    plan_id: str,
    timeout_seconds: int = 120,
    cwd: Path | None = None,
) -> VerificationRun:
    plan = load_plan(plan_id, cwd)
    if not plan.validation_checklist:
        raise AbhError("plan has no validation checklist")
    if timeout_seconds <= 0:
        raise AbhError("timeout must be greater than zero")

    root = Path.cwd() if cwd is None else Path(cwd)
    artifacts: list[str] = []
    failed_checks: list[str] = []
    commands = list(plan.validation_checklist)

    for command in commands:
        if is_recursive_verify_command(command, plan_id):
            artifacts.append(f"command={command!r}; exit_code=recursive_verify_guard")
            failed_checks.append(command)
            continue
        started = time.perf_counter()
        try:
            completed = subprocess.run(
                command,
                cwd=root,
                shell=True,
                text=True,
                capture_output=True,
                timeout=timeout_seconds,
                check=False,
            )
            duration = time.perf_counter() - started
            stdout = completed.stdout.strip().replace("\n", "\\n")[:500]
            stderr = completed.stderr.strip().replace("\n", "\\n")[:500]
            artifacts.append(
                f"command={command!r}; exit_code={completed.returncode}; duration_seconds={duration:.3f}; "
                f"stdout={stdout!r}; stderr={stderr!r}"
            )
            if completed.returncode != 0:
                failed_checks.append(command)
        except subprocess.TimeoutExpired as exc:
            duration = time.perf_counter() - started
            stdout = (exc.stdout or "").strip().replace("\n", "\\n")[:500] if isinstance(exc.stdout, str) else ""
            stderr = (exc.stderr or "").strip().replace("\n", "\\n")[:500] if isinstance(exc.stderr, str) else ""
            artifacts.append(
                f"command={command!r}; exit_code=timeout; duration_seconds={duration:.3f}; "
                f"timeout_seconds={timeout_seconds}; stdout={stdout!r}; stderr={stderr!r}"
            )
            failed_checks.append(command)

    result = "pass" if not failed_checks else "fail"
    return record_verification(
        plan_id=plan_id,
        command=" && ".join(commands),
        result=result,
        artifacts=artifacts,
        failed_checks=failed_checks,
        cwd=cwd,
    )


def render_plan_markdown(plan: PlanRecord) -> str:
    def bullet_lines(values: list[str]) -> str:
        if not values:
            return "- "
        return "\n".join(f"- {value}" for value in values)

    return (
        f"# Plan: {plan.title}\n\n"
        "## Metadata\n\n"
        f"- ID: {plan.id}\n"
        f"- Status: {plan.status}\n"
        f"- Attractor: {plan.attractor}\n"
        f"- Baseline: {plan.baseline}\n"
        f"- Owner: {plan.owner}\n"
        f"- Created: {plan.created_at}\n"
        f"- Updated: {plan.updated_at}\n\n"
        "## Goals\n\n"
        f"{bullet_lines(plan.goals)}\n\n"
        "## Non-Goals\n\n"
        f"{bullet_lines(plan.non_goals)}\n\n"
        "## Exit Criteria\n\n"
        f"{bullet_lines(plan.exit_criteria)}\n\n"
        "## Validation Checklist\n\n"
        f"{bullet_lines(plan.validation_checklist)}\n\n"
        "## Closure Evidence\n\n"
        f"{bullet_lines(plan.closure_evidence)}\n\n"
        "## Verification Runs\n\n"
        f"{bullet_lines(plan.verification_runs)}\n\n"
        "## Audits\n\n"
        f"{bullet_lines(plan.audit_ids)}\n"
    )


def plan_status_line(plan: PlanRecord) -> str:
    latest = plan.verification_runs[-1] if plan.verification_runs else "none"
    return (
        f"{plan.id} [{plan.status}]\n"
        f"title: {plan.title}\n"
        f"attractor: {plan.attractor}\n"
        f"baseline: {plan.baseline}\n"
        f"verification_runs: {len(plan.verification_runs)}\n"
        f"latest_verification: {latest}\n"
        f"audits: {len(plan.audit_ids)}"
    )


def parse_finding(value: str) -> AuditFinding:
    parts = value.split("|", 3)
    if len(parts) != 4 or not all(part.strip() for part in parts):
        raise AbhError("finding must use Severity|Finding|Evidence|Recommendation")
    return AuditFinding(
        severity=parts[0].strip(),
        finding=parts[1].strip(),
        evidence=parts[2].strip(),
        recommendation=parts[3].strip(),
    )


def load_audit(audit_id: str, cwd: Path | None = None) -> AuditRecord:
    validate_identifier(audit_id, "audit id")
    path = audit_json_path(audit_id, cwd)
    if not path.exists():
        raise AbhError(f"audit not found: {audit_id}")
    return AuditRecord.from_dict(read_json(path))


def list_audits(cwd: Path | None = None) -> list[AuditRecord]:
    directory = audits_dir(cwd)
    if not directory.exists():
        return []
    audits: list[AuditRecord] = []
    for path in sorted(directory.glob("*.json")):
        audits.append(AuditRecord.from_dict(read_json(path)))
    return audits


def save_audit(audit: AuditRecord, cwd: Path | None = None, write_doc: bool = True) -> AuditRecord:
    ensure_workspace(cwd)
    audit.updated_at = utc_now()
    if write_doc:
        doc_path = audit.doc_path or str(audit_doc_path(audit.id, cwd))
        audit.doc_path = doc_path
        doc_file = Path(doc_path)
        doc_file.parent.mkdir(parents=True, exist_ok=True)
        doc_file.write_text(render_audit_markdown(audit), encoding="utf-8")
    write_json(audit_json_path(audit.id, cwd), audit.to_dict())
    return audit


def request_audit(
    *,
    audit_id: str,
    plan_id: str,
    auditor: str,
    scope: str,
    evidence: list[str] | None = None,
    cwd: Path | None = None,
) -> AuditRecord:
    ensure_workspace(cwd)
    validate_identifier(audit_id, "audit id")
    plan = load_plan(plan_id, cwd)
    if audit_json_path(audit_id, cwd).exists():
        raise AbhError(f"audit already exists: {audit_id}")
    reviewed = list(evidence or [])
    if not reviewed:
        raise AbhError("audit request requires at least one evidence item")
    audit = AuditRecord(
        id=audit_id,
        plan_id=plan_id,
        auditor=auditor,
        scope=scope,
        evidence=reviewed,
        doc_path=str(audit_doc_path(audit_id, cwd)),
    )
    save_audit(audit, cwd)
    if audit_id not in plan.audit_ids:
        plan.audit_ids.append(audit_id)
        save_plan(plan, cwd)
    return audit


def record_audit(
    *,
    audit_id: str,
    result: str,
    rationale: str,
    findings: list[str] | None = None,
    follow_ups: list[str] | None = None,
    cwd: Path | None = None,
) -> AuditRecord:
    if result not in AUDIT_RESULTS:
        raise AbhError(f"invalid audit result: {result}")
    audit = load_audit(audit_id, cwd)
    audit.result = result
    audit.rationale = rationale
    audit.status = "complete"
    audit.findings = [parse_finding(value) for value in (findings or [])]
    audit.follow_ups = list(follow_ups or [])
    return save_audit(audit, cwd)


def close_plan(plan_id: str, cwd: Path | None = None) -> PlanRecord:
    plan = load_plan(plan_id, cwd)
    passing_audit = None
    for audit_id in plan.audit_ids:
        audit = load_audit(audit_id, cwd)
        if audit.result == "pass" and audit.status == "complete":
            passing_audit = audit
    if passing_audit is None:
        raise AbhError("cannot close plan without a passing audit")
    if not plan.closure_evidence:
        raise AbhError("cannot close plan without closure evidence")
    plan.status = "closed"
    if passing_audit.id not in plan.closure_evidence:
        plan.closure_evidence.append(passing_audit.id)
    return save_plan(plan, cwd)


def render_audit_markdown(audit: AuditRecord) -> str:
    def bullet_lines(values: list[str]) -> str:
        if not values:
            return "- "
        return "\n".join(f"- {value}" for value in values)

    if audit.findings:
        finding_lines = "\n".join(
            f"| {finding.severity} | {finding.finding} | {finding.evidence} | {finding.recommendation} |"
            for finding in audit.findings
        )
    else:
        finding_lines = "|  |  |  |  |"
    return (
        f"# Audit: {audit.plan_id}\n\n"
        "## Metadata\n\n"
        f"- Audit ID: {audit.id}\n"
        f"- Plan: {audit.plan_id}\n"
        f"- Auditor: {audit.auditor}\n"
        f"- Status: {audit.status}\n"
        f"- Created: {audit.created_at}\n"
        f"- Updated: {audit.updated_at}\n\n"
        "## Scope\n\n"
        f"{audit.scope}\n\n"
        "## Evidence Reviewed\n\n"
        f"{bullet_lines(audit.evidence)}\n\n"
        "## Findings\n\n"
        "| Severity | Finding | Evidence | Recommendation |\n"
        "| --- | --- | --- | --- |\n"
        f"{finding_lines}\n\n"
        "## Verdict\n\n"
        f"- Result: {audit.result}\n"
        f"- Rationale: {audit.rationale}\n\n"
        "## Follow-Ups\n\n"
        f"{bullet_lines(audit.follow_ups)}\n"
    )


def load_memory(memory_id: str, cwd: Path | None = None) -> MemoryRecord:
    validate_identifier(memory_id, "memory id")
    path = memory_json_path(memory_id, cwd)
    if not path.exists():
        raise AbhError(f"memory not found: {memory_id}")
    return MemoryRecord.from_dict(read_json(path))


def save_memory(memory: MemoryRecord, cwd: Path | None = None, write_doc: bool = True) -> MemoryRecord:
    ensure_workspace(cwd)
    memory.updated_at = utc_now()
    if write_doc:
        doc_path = memory.doc_path or str(memory_doc_path(memory.id, cwd))
        memory.doc_path = doc_path
        doc_file = Path(doc_path)
        doc_file.parent.mkdir(parents=True, exist_ok=True)
        doc_file.write_text(render_memory_markdown(memory), encoding="utf-8")
    write_json(memory_json_path(memory.id, cwd), memory.to_dict())
    return memory


def add_memory(
    *,
    memory_id: str,
    memory_type: str,
    summary: str,
    context: str,
    implication: str,
    evidence: list[str] | None = None,
    related: list[str] | None = None,
    deprecation_policy: str | None = None,
    cwd: Path | None = None,
) -> MemoryRecord:
    ensure_workspace(cwd)
    validate_identifier(memory_id, "memory id")
    if memory_type not in MEMORY_TYPES:
        raise AbhError(f"invalid memory type: {memory_type}")
    if memory_json_path(memory_id, cwd).exists():
        raise AbhError(f"memory already exists: {memory_id}")
    evidence_items = list(evidence or [])
    if not evidence_items:
        raise AbhError("memory requires at least one evidence item")
    memory = MemoryRecord(
        id=memory_id,
        memory_type=memory_type,
        summary=summary,
        context=context,
        implication=implication,
        related=list(related or []),
        evidence=evidence_items,
        deprecation_policy=deprecation_policy or "Mark deprecated when evidence no longer applies.",
        doc_path=str(memory_doc_path(memory_id, cwd)),
    )
    return save_memory(memory, cwd)


def search_memory(
    *,
    memory_type: str | None = None,
    query: str | None = None,
    cwd: Path | None = None,
) -> list[MemoryRecord]:
    if memory_type and memory_type not in MEMORY_TYPES:
        raise AbhError(f"invalid memory type: {memory_type}")
    directory = memory_dir(cwd)
    if not directory.exists():
        return []
    normalized_query = (query or "").strip().lower()
    results: list[MemoryRecord] = []
    for path in sorted(directory.glob("*.json")):
        memory = MemoryRecord.from_dict(read_json(path))
        if memory_type and memory.memory_type != memory_type:
            continue
        searchable = "\n".join(
            [
                memory.id,
                memory.memory_type,
                memory.summary,
                memory.context,
                memory.implication,
                "\n".join(memory.related),
                "\n".join(memory.evidence),
            ]
        ).lower()
        if normalized_query and normalized_query not in searchable:
            continue
        results.append(memory)
    return results


def list_memories(cwd: Path | None = None) -> list[MemoryRecord]:
    directory = memory_dir(cwd)
    if not directory.exists():
        return []
    memories: list[MemoryRecord] = []
    for path in sorted(directory.glob("*.json")):
        memories.append(MemoryRecord.from_dict(read_json(path)))
    return memories


def render_memory_markdown(memory: MemoryRecord) -> str:
    def bullet_lines(values: list[str]) -> str:
        if not values:
            return "- "
        return "\n".join(f"- {value}" for value in values)

    return (
        f"# Memory: {memory.summary}\n\n"
        "## Metadata\n\n"
        f"- ID: {memory.id}\n"
        f"- Type: {memory.memory_type}\n"
        f"- Status: {memory.status}\n"
        f"- Created: {memory.created_at}\n"
        f"- Updated: {memory.updated_at}\n"
        f"- Related: {', '.join(memory.related)}\n\n"
        "## Summary\n\n"
        f"{memory.summary}\n\n"
        "## Context\n\n"
        f"{memory.context}\n\n"
        "## Evidence\n\n"
        f"{bullet_lines(memory.evidence)}\n\n"
        "## Implication\n\n"
        f"{memory.implication}\n\n"
        "## Deprecation Policy\n\n"
        f"{memory.deprecation_policy}\n"
    )


ROUTES: dict[str, dict[str, object]] = {
    "completion_audit": {
        "keywords": ("close", "closed", "completion", "完成", "关闭", "验收", "审计", "audit"),
        "reading_order": [
            "docs/plans/",
            "docs/audits/",
            "docs/memory/",
            "tests/",
            "abh/",
        ],
        "rationale": "Completion questions are decided by plan criteria, independent audit, memory, tests, and code evidence.",
    },
    "implementation": {
        "keywords": ("implement", "code", "cli", "命令", "实现", "开发"),
        "reading_order": [
            "docs/architecture/attractors/",
            "docs/plans/",
            "abh/",
            "tests/",
        ],
        "rationale": "Implementation questions should start from attractor and plan intent, then inspect code and tests.",
    },
    "drift": {
        "keywords": ("drift", "偏离", "漂移", "scope", "boundary", "dependency", "术语"),
        "reading_order": [
            "docs/architecture/attractors/",
            "docs/plans/",
            "docs/memory/",
            "docs/drift/",
            "abh/",
        ],
        "rationale": "Drift questions compare the attractor and plan against observed changes and prior memory.",
    },
}


def route_question(question: str) -> dict[str, object]:
    text = question.lower()
    for route_name, route in ROUTES.items():
        if any(keyword.lower() in text for keyword in route["keywords"]):
            reading_order = list(route["reading_order"])
            # inject active plans
            plans = list_plans()
            active = [p for p in plans if p.status in ("running", "blocked")]
            if active:
                reading_order.append("docs/plans/ (active plans)")
                for p in active:
                    reading_order.append(f"  -> {p.id} [{p.status}]")
            # inject recent memories
            memories = list_memories()
            question_words = set(text.split())
            relevant = []
            for m in memories:
                mem_text = f"{m.summary} {m.context} {m.implication}".lower()
                if any(w in mem_text for w in question_words if len(w) > 2):
                    relevant.append(m)
            if relevant:
                reading_order.append("docs/memory/ (relevant memories)")
                for m in relevant[:5]:
                    reading_order.append(f"  -> {m.id} [{m.memory_type}]")

            return {
                "route": route_name,
                "reading_order": reading_order,
                "active_plans": len(active),
                "rationale": route["rationale"],
            }
    return {
        "route": "general",
        "reading_order": [
            "docs/architecture/attractors/",
            "docs/plans/",
            "docs/audits/",
            "docs/memory/",
            "abh/",
            "tests/",
        ],
        "rationale": "General questions should be grounded in attractor, plan, audit, memory, code, and tests.",
    }


DRIFT_RULES: dict[str, dict[str, object]] = {
    "boundary_drift": {
        "keywords": ("boundary", "module boundary", "moved", "mixed", "plan manager", "audit logic", "边界", "混入"),
        "recommendation": "Create a follow-up to restore ownership boundaries or update the attractor if the boundary changed intentionally.",
    },
    "dependency_drift": {
        "keywords": ("dependency", "database", "remote", "external", "service", "package", "依赖", "数据库", "外部"),
        "recommendation": "Review plan non-goals and dependency rules before accepting the new dependency.",
    },
    "test_drift": {
        "keywords": ("skip test", "skipped tests", "without tests", "no test", "测试跳过", "未测试"),
        "recommendation": "Add or restore verification coverage before closing the plan.",
    },
    "terminology_drift": {
        "keywords": ("renamed", "terminology", "term", "prepared", "ready", "术语", "重命名"),
        "recommendation": "Align terminology with canonical docs or record an explicit migration.",
    },
}


def analyze_drift_text(text: str) -> list[DriftFinding]:
    lowered = text.lower()
    findings: list[DriftFinding] = []
    for drift_type, rule in DRIFT_RULES.items():
        matched = [keyword for keyword in rule["keywords"] if keyword.lower() in lowered]
        if matched:
            findings.append(
                DriftFinding(
                    drift_type=drift_type,
                    evidence=f"matched keywords: {', '.join(matched)}",
                    recommendation=str(rule["recommendation"]),
                )
            )
    return findings


def save_drift_report(report: DriftReport, cwd: Path | None = None, write_doc: bool = True) -> DriftReport:
    ensure_workspace(cwd)
    report.updated_at = utc_now()
    if write_doc:
        doc_path = report.doc_path or str(drift_doc_path(report.id, cwd))
        report.doc_path = doc_path
        doc_file = Path(doc_path)
        doc_file.parent.mkdir(parents=True, exist_ok=True)
        doc_file.write_text(render_drift_markdown(report), encoding="utf-8")
    write_json(drift_json_path(report.id, cwd), report.to_dict())
    return report


def analyze_drift(
    *,
    drift_id: str,
    source: str,
    evidence: list[str] | None = None,
    memory_id: str | None = None,
    plan_id: str | None = None,
    cwd: Path | None = None,
) -> DriftReport:
    validate_identifier(drift_id, "drift id")
    source_path = Path(source)
    if not source_path.exists():
        raise AbhError(f"drift source not found: {source}")
    source_text = source_path.read_text(encoding="utf-8")
    findings = analyze_drift_text(source_text)
    # plan-based drift detection
    if plan_id:
        plan = load_plan(plan_id, cwd)
        negation_prefixes = ("不", "不要", "无需", "禁止", "避免", "no ", "not ")
        lowered = source_text.lower()
        for non_goal in plan.non_goals:
            clean = non_goal.lower()
            for prefix in negation_prefixes:
                if clean.startswith(prefix):
                    clean = clean[len(prefix):]
                    break
            keywords = [clean] if len(clean) > 2 else []
            keywords += [w for w in clean.split() if len(w) > 2 and w not in keywords]
            if not keywords:
                continue
            matched = [kw for kw in keywords if kw in lowered]
            if matched:
                existing_types = {f.drift_type for f in findings}
                for dt in DRIFT_TYPES:
                    if dt not in existing_types:
                        findings.append(
                            DriftFinding(
                                drift_type=dt,
                                evidence=f"plan non-goal violation: '{non_goal}' matched keywords {matched}",
                                recommendation=f"Review plan '{plan_id}' non-goal: {non_goal}. Consider updating plan or source.",
                            )
                        )
                        break
    follow_ups = [finding.recommendation for finding in findings]
    report = DriftReport(
        id=drift_id,
        source=source,
        findings=findings,
        evidence=list(evidence or [source]),
        follow_ups=follow_ups,
        doc_path=str(drift_doc_path(drift_id, cwd)),
    )
    save_drift_report(report, cwd)
    if memory_id:
        if not findings:
            raise AbhError("cannot write drift memory without drift findings")
        add_memory(
            memory_id=memory_id,
            memory_type="divergent_pattern",
            summary=f"Drift report {drift_id}: {', '.join(finding.drift_type for finding in findings)}",
            context=f"Drift source: {source}",
            implication="Use these drift patterns to route follow-up plans before closure.",
            evidence=[str(drift_doc_path(drift_id, cwd))],
            related=[drift_id],
            cwd=cwd,
        )
    return report


def render_drift_markdown(report: DriftReport) -> str:
    def bullet_lines(values: list[str]) -> str:
        if not values:
            return "- "
        return "\n".join(f"- {value}" for value in values)

    if report.findings:
        finding_lines = "\n".join(
            f"| {finding.drift_type} | {finding.evidence} | {finding.recommendation} |"
            for finding in report.findings
        )
    else:
        finding_lines = "|  |  |  |"
    return (
        f"# Drift: {report.id}\n\n"
        "## Metadata\n\n"
        f"- ID: {report.id}\n"
        f"- Source: {report.source}\n"
        f"- Created: {report.created_at}\n"
        f"- Updated: {report.updated_at}\n\n"
        "## Evidence\n\n"
        f"{bullet_lines(report.evidence)}\n\n"
        "## Findings\n\n"
        "| Type | Evidence | Recommendation |\n"
        "| --- | --- | --- |\n"
        f"{finding_lines}\n\n"
        "## Follow-Ups\n\n"
        f"{bullet_lines(report.follow_ups)}\n"
    )
