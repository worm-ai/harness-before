from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from .audits import (
    list_audits,
    load_audit,
    parse_finding,
    record_audit,
    render_audit_markdown,
    request_audit,
    save_audit,
)
from .attractors import (
    active_attractor,
    create_attractor,
    is_active_attractor_reference,
    list_attractors,
    load_attractor,
    render_attractor_markdown,
    save_attractor,
    seed_active_attractor_from_document,
    supersede_attractor,
)
from .drift import (
    DRIFT_RULES,
    analyze_drift,
    analyze_drift_text,
    render_drift_markdown,
    save_drift_report,
)
from .errors import AbhError, validate_identifier
from .memory import (
    add_memory,
    list_memories,
    load_memory,
    render_memory_markdown,
    save_memory,
    search_memory,
)
from .plans import (
    ALLOWED_TRANSITIONS,
    append_unique,
    close_plan,
    create_plan,
    list_plans,
    load_plan,
    plan_status_line,
    render_plan_markdown,
    save_plan,
    transition_plan,
    update_plan_record,
    validate_plan_ready,
)
from .roadmap import (
    check_plan_numbering,
    check_roadmap_queue,
    list_roadmap_items,
    load_roadmap_queue,
    materialize_roadmap_item,
    next_plan_id,
    next_plan_sequence,
    save_roadmap_queue,
)
from .routing import ROUTES, route_question
from .storage import (
    audits_dir,
    attractors_dir,
    drift_dir,
    docs_audits_dir,
    docs_attractors_dir,
    docs_drift_dir,
    docs_memory_dir,
    docs_plans_dir,
    memory_dir,
    plans_dir,
    read_json,
)
from .verifications import is_recursive_verify_command, load_verification, record_verification, run_verification


# Verification runs are JSON-only execution evidence today, so doctor excludes
# them from JSON/Markdown consistency checks until they get a document model.
DOCTOR_OBJECTS: tuple[tuple[str, str, Callable[[Path | None], Path], Callable[[Path | None], Path]], ...] = (
    ("plan", "plan-", plans_dir, docs_plans_dir),
    ("audit", "audit-", audits_dir, docs_audits_dir),
    ("attractor", "attractor-", attractors_dir, docs_attractors_dir),
    ("memory", "mem-", memory_dir, docs_memory_dir),
    ("drift", "drift-", drift_dir, docs_drift_dir),
)


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
                if label == "attractor":
                    doc_path = data.get("doc_path") or data.get("path")
                    if isinstance(doc_path, str) and doc_path and not Path(doc_path).exists():
                        issues.append(f"missing markdown for attractor {path.stem}")
        doc_ids = set()
        if docs_dir.exists():
            doc_ids = {
                path.stem
                for path in docs_dir.glob("*.md")
                if path.name != "README.md" and path.stem.startswith(prefix)
            }
        if label == "attractor":
            continue
        for object_id in sorted(json_ids - doc_ids):
            issues.append(f"missing markdown for {label} {object_id}")
        for object_id in sorted(doc_ids - json_ids):
            issues.append(f"orphan markdown for {label} {object_id}")
    issues.extend(check_plan_numbering(cwd))
    issues.extend(check_roadmap_queue(cwd))
    return issues
