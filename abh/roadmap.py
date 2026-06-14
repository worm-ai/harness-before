from __future__ import annotations

import re
from pathlib import Path

from .errors import AbhError, validate_identifier
from .models import PlanRecord, RoadmapItem, RoadmapQueue, SCHEMA_VERSION
from .plans import create_plan, list_plans
from .storage import abh_dir, ensure_workspace, file_lock, plans_dir, read_json, roadmap_path, write_json

LEGACY_DUPLICATE_PLAN_SEQUENCES = {"007"}
PLAN_SEQUENCE_RE = re.compile(r"^plan-(\d+)(?:-|$)")
PREASSIGNED_PLAN_ID_FIELDS = ("planned_plan_id", "reserved_plan_id", "next_plan_id")


def load_roadmap_queue(cwd: Path | None = None) -> RoadmapQueue:
    path = roadmap_path(cwd)
    if not path.exists():
        return RoadmapQueue()
    return RoadmapQueue.from_dict(read_json(path))


def save_roadmap_queue(queue: RoadmapQueue, cwd: Path | None = None) -> RoadmapQueue:
    ensure_workspace(cwd)
    write_json(roadmap_path(cwd), queue.to_dict())
    return queue


def plan_sequence(plan_id: str) -> int | None:
    match = PLAN_SEQUENCE_RE.match(plan_id)
    if match is None:
        return None
    return int(match.group(1))


def next_plan_sequence(cwd: Path | None = None) -> int:
    sequences = [sequence for sequence in (plan_sequence(plan.id) for plan in list_plans(cwd)) if sequence is not None]
    return max(sequences, default=0) + 1


def next_plan_id(cwd: Path | None = None) -> str:
    return f"plan-{next_plan_sequence(cwd):03d}"


def slug_from_key(key: str) -> str:
    slug = key.split(".")[-1].strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug).strip("-")
    if not slug:
        raise AbhError(f"roadmap item key has no slug: {key}")
    return slug


def materialized_plan_id(key: str, cwd: Path | None = None) -> str:
    validate_identifier(key, "roadmap item key")
    return f"{next_plan_id(cwd)}-{slug_from_key(key)}"


def get_roadmap_item(key: str, cwd: Path | None = None) -> RoadmapItem:
    validate_identifier(key, "roadmap item key")
    queue = load_roadmap_queue(cwd)
    for item in queue.items:
        if item.key == key:
            return item
    raise AbhError(f"roadmap item not found: {key}")


def list_roadmap_items(cwd: Path | None = None) -> list[RoadmapItem]:
    return list(load_roadmap_queue(cwd).items)


def check_roadmap_queue(cwd: Path | None = None) -> list[str]:
    path = roadmap_path(cwd)
    if not path.exists():
        return []
    data = read_json(path)
    issues: list[str] = []
    if not data.get("schema_version"):
        issues.append("missing schema_version for roadmap queue")
    keys: set[str] = set()
    for raw_item in data.get("items", []):
        key = raw_item.get("key")
        if not isinstance(key, str) or not key.strip():
            issues.append("roadmap item missing key")
            continue
        if key in keys:
            issues.append(f"duplicate roadmap item key {key}")
        keys.add(key)
        for field in PREASSIGNED_PLAN_ID_FIELDS:
            value = raw_item.get(field)
            if isinstance(value, str) and value.startswith("plan-"):
                issues.append(f"roadmap item {key} must not preassign plan id {value}")
        plan_id = raw_item.get("plan_id")
        status = raw_item.get("status", "queued")
        if status == "queued" and plan_id is not None:
            issues.append(f"queued roadmap item {key} must have null plan_id")
        if plan_id is not None and not roadmap_path(cwd).parent.joinpath("plans", f"{plan_id}.json").exists():
            issues.append(f"roadmap item {key} references missing materialized plan {plan_id}")
    return issues


def check_plan_numbering(cwd: Path | None = None) -> list[str]:
    seen: dict[str, list[str]] = {}
    directory = plans_dir(cwd)
    if not directory.exists():
        return []
    for path in sorted(directory.glob("*.json")):
        data = read_json(path)
        plan_id = data.get("id", path.stem)
        if not isinstance(plan_id, str):
            continue
        match = PLAN_SEQUENCE_RE.match(plan_id)
        if match is None:
            continue
        sequence = match.group(1)
        seen.setdefault(sequence, []).append(plan_id)
    issues: list[str] = []
    for sequence, plan_ids in sorted(seen.items()):
        if sequence in LEGACY_DUPLICATE_PLAN_SEQUENCES:
            continue
        if len(plan_ids) > 1:
            issues.append(f"duplicate plan sequence {sequence}: {', '.join(sorted(plan_ids))}")
    return issues


def materialize_roadmap_item(key: str, cwd: Path | None = None) -> tuple[RoadmapItem, PlanRecord]:
    validate_identifier(key, "roadmap item key")
    ensure_workspace(cwd)
    with file_lock(abh_dir(cwd) / "roadmap.materialize"):
        queue = load_roadmap_queue(cwd)
        for item in queue.items:
            if item.key != key:
                continue
            raw_items = read_json(roadmap_path(cwd)).get("items", []) if roadmap_path(cwd).exists() else []
            for raw_item in raw_items:
                if raw_item.get("key") == key:
                    for field in PREASSIGNED_PLAN_ID_FIELDS:
                        value = raw_item.get(field)
                        if isinstance(value, str) and value.startswith("plan-"):
                            raise AbhError(f"roadmap item {key} must not preassign plan id {value}")
            if item.plan_id:
                raise AbhError(f"roadmap item already materialized: {key} -> {item.plan_id}")
            plan_id = materialized_plan_id(item.key, cwd)
            plan = create_plan(
                plan_id=plan_id,
                title=item.title,
                attractor=item.attractor,
                baseline=item.baseline or item.summary,
                status="draft",
                goals=item.goals,
                non_goals=item.non_goals,
                exit_criteria=item.exit_criteria,
                validation_checklist=item.validation_checklist,
                closure_evidence=item.closure_evidence,
                cwd=cwd,
            )
            item.plan_id = plan.id
            item.status = "materialized"
            save_roadmap_queue(queue, cwd)
            return item, plan
    raise AbhError(f"roadmap item not found: {key}")
