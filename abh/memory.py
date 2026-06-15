from __future__ import annotations

from pathlib import Path

from .errors import AbhError, validate_identifier
from .models import MEMORY_STATUSES, MEMORY_TYPES, MemoryRecord, utc_now
from .storage import ensure_workspace, memory_doc_path, memory_json_path, memory_dir, read_json, write_json, write_json_markdown_pair


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
        write_json_markdown_pair(memory_json_path(memory.id, cwd), memory.to_dict(), Path(doc_path), render_memory_markdown(memory))
    else:
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
    tags: list[str] | None = None,
    status: str = "active",
    related_plan_ids: list[str] | None = None,
    related_audit_ids: list[str] | None = None,
    related_drift_ids: list[str] | None = None,
    superseded_by: str | None = None,
    deprecation_policy: str | None = None,
    cwd: Path | None = None,
) -> MemoryRecord:
    ensure_workspace(cwd)
    validate_identifier(memory_id, "memory id")
    if memory_type not in MEMORY_TYPES:
        raise AbhError(f"invalid memory type: {memory_type}")
    if status not in MEMORY_STATUSES:
        raise AbhError(f"invalid memory status: {status}")
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
        status=status,
        related=list(related or []),
        evidence=evidence_items,
        tags=list(tags or []),
        related_plan_ids=list(related_plan_ids or []),
        related_audit_ids=list(related_audit_ids or []),
        related_drift_ids=list(related_drift_ids or []),
        superseded_by=superseded_by or "",
        deprecation_policy=deprecation_policy or "Mark deprecated when evidence no longer applies.",
        doc_path=str(memory_doc_path(memory_id, cwd)),
    )
    return save_memory(memory, cwd)


def search_memory(
    *,
    memory_type: str | None = None,
    query: str | None = None,
    status: str | None = None,
    tag: str | None = None,
    related_plan_id: str | None = None,
    related_audit_id: str | None = None,
    related_drift_id: str | None = None,
    cwd: Path | None = None,
) -> list[MemoryRecord]:
    if memory_type and memory_type not in MEMORY_TYPES:
        raise AbhError(f"invalid memory type: {memory_type}")
    if status and status not in MEMORY_STATUSES:
        raise AbhError(f"invalid memory status: {status}")
    directory = memory_dir(cwd)
    if not directory.exists():
        return []
    normalized_query = (query or "").strip().lower()
    normalized_tag = (tag or "").strip().lower()
    results: list[MemoryRecord] = []
    for path in sorted(directory.glob("*.json")):
        memory = MemoryRecord.from_dict(read_json(path))
        if memory_type and memory.memory_type != memory_type:
            continue
        if status and memory.status != status:
            continue
        if normalized_tag and normalized_tag not in {item.lower() for item in memory.tags}:
            continue
        if related_plan_id and related_plan_id not in memory.related_plan_ids:
            continue
        if related_audit_id and related_audit_id not in memory.related_audit_ids:
            continue
        if related_drift_id and related_drift_id not in memory.related_drift_ids:
            continue
        searchable = "\n".join(
            [
                memory.id,
                memory.memory_type,
                memory.summary,
                memory.context,
                memory.implication,
                memory.status,
                "\n".join(memory.related),
                "\n".join(memory.evidence),
                "\n".join(memory.tags),
                "\n".join(memory.related_plan_ids),
                "\n".join(memory.related_audit_ids),
                "\n".join(memory.related_drift_ids),
                memory.superseded_by,
            ]
        ).lower()
        if normalized_query and normalized_query not in searchable:
            continue
        results.append(memory)
    return results


def list_memories(cwd: Path | None = None, *, limit: int | None = None, offset: int = 0) -> list[MemoryRecord]:
    directory = memory_dir(cwd)
    if not directory.exists():
        return []
    memories: list[MemoryRecord] = []
    for path in sorted(directory.glob("*.json")):
        memories.append(MemoryRecord.from_dict(read_json(path)))
    if offset:
        memories = memories[offset:]
    if limit is not None:
        memories = memories[:limit]
    return memories


def update_memory(
    *,
    memory_id: str,
    add_tags: list[str] | None = None,
    add_related_plan_ids: list[str] | None = None,
    add_related_audit_ids: list[str] | None = None,
    add_related_drift_ids: list[str] | None = None,
    status: str | None = None,
    cwd: Path | None = None,
) -> MemoryRecord:
    """Update an existing memory record by appending tags and/or relationships."""
    validate_identifier(memory_id, "memory id")
    path = memory_json_path(memory_id, cwd)
    if not path.exists():
        raise AbhError(f"memory not found: {memory_id}")
    memory = MemoryRecord.from_dict(read_json(path))
    if add_tags:
        for tag in add_tags:
            if tag not in memory.tags:
                memory.tags.append(tag)
    if add_related_plan_ids:
        for pid in add_related_plan_ids:
            if pid not in memory.related_plan_ids:
                memory.related_plan_ids.append(pid)
    if add_related_audit_ids:
        for aid in add_related_audit_ids:
            if aid not in memory.related_audit_ids:
                memory.related_audit_ids.append(aid)
    if add_related_drift_ids:
        for did in add_related_drift_ids:
            if did not in memory.related_drift_ids:
                memory.related_drift_ids.append(did)
    if status is not None and status in MEMORY_STATUSES:
        memory.status = status
    return save_memory(memory, cwd)


def triage_memories(cwd: Path | None = None) -> list[dict[str, object]]:
    """Return orphaned active memories with triage guidance.

    An orphaned memory is active but has no tags or no typed relationships
    (related_plan_ids, related_audit_ids, related_drift_ids all empty).
    """
    all_memories = list_memories(cwd)
    orphaned: list[dict[str, object]] = []
    for mem in all_memories:
        if mem.status != "active":
            continue
        has_tags = bool(mem.tags)
        has_relations = bool(mem.related_plan_ids or mem.related_audit_ids or mem.related_drift_ids)
        if not has_tags or not has_relations:
            orphaned.append({
                "id": mem.id,
                "memory_type": mem.memory_type,
                "summary": mem.summary,
                "has_tags": has_tags,
                "has_relations": has_relations,
                "tags": mem.tags,
                "related_plan_ids": mem.related_plan_ids,
                "related_audit_ids": mem.related_audit_ids,
                "related_drift_ids": mem.related_drift_ids,
                "recommended_action": (
                    "dismiss" if not has_tags and not has_relations
                    else "add_tags" if not has_tags
                    else "add_relations"
                ),
            })
    # Sort: most orphaned first (no tags AND no relations)
    orphaned.sort(key=lambda m: (m["has_tags"], m["has_relations"]))
    return orphaned


def render_memory_markdown(memory: MemoryRecord) -> str:
    def bullet_lines(values: list[str]) -> str:
        if not values:
            return "-"
        return "\n".join(f"- {value}" for value in values)

    return (
        f"# Memory: {memory.summary}\n\n"
        "## Metadata\n\n"
        f"- ID: {memory.id}\n"
        f"- Type: {memory.memory_type}\n"
        f"- Status: {memory.status}\n"
        f"- Tags: {', '.join(memory.tags)}\n"
        f"- Created: {memory.created_at}\n"
        f"- Updated: {memory.updated_at}\n"
        f"- Related: {', '.join(memory.related)}\n"
        f"- Related Plans: {', '.join(memory.related_plan_ids)}\n"
        f"- Related Audits: {', '.join(memory.related_audit_ids)}\n"
        f"- Related Drift Reports: {', '.join(memory.related_drift_ids)}\n"
        f"- Superseded By: {memory.superseded_by}\n\n"
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
