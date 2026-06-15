from __future__ import annotations

from pathlib import Path

from .errors import AbhError, validate_identifier
from .models import AttractorRecord, utc_now
from .storage import (
    attractor_doc_path,
    attractor_json_path,
    attractors_dir,
    docs_attractors_dir,
    ensure_workspace,
    read_json,
    write_json,
    write_json_markdown_pair,
)


def list_attractors(cwd: Path | None = None) -> list[AttractorRecord]:
    directory = attractors_dir(cwd)
    if not directory.exists():
        return []
    attractors: list[AttractorRecord] = []
    for path in sorted(directory.glob("*.json")):
        attractors.append(AttractorRecord.from_dict(read_json(path)))
    return attractors


def load_attractor(attractor_id: str, cwd: Path | None = None) -> AttractorRecord:
    validate_identifier(attractor_id, "attractor id")
    path = attractor_json_path(attractor_id, cwd)
    if not path.exists():
        raise AbhError(f"attractor not found: {attractor_id}")
    return AttractorRecord.from_dict(read_json(path))


def active_attractor(cwd: Path | None = None) -> AttractorRecord:
    active = [attractor for attractor in list_attractors(cwd) if attractor.status == "active"]
    if not active:
        raise AbhError("active attractor not found")
    if len(active) > 1:
        ids = ", ".join(attractor.id for attractor in active)
        raise AbhError(f"multiple active attractors found: {ids}")
    return active[0]


def save_attractor(attractor: AttractorRecord, cwd: Path | None = None, write_doc: bool = True) -> AttractorRecord:
    ensure_workspace(cwd)
    attractor.updated_at = utc_now()
    if write_doc:
        doc_path = attractor.doc_path or attractor.path or str(attractor_doc_path(attractor.id, cwd))
        attractor.doc_path = doc_path
        attractor.path = doc_path
        write_json_markdown_pair(attractor_json_path(attractor.id, cwd), attractor.to_dict(), Path(doc_path), render_attractor_markdown(attractor))
    else:
        write_json(attractor_json_path(attractor.id, cwd), attractor.to_dict())
    return attractor


def deactivate_active_attractors(cwd: Path | None = None) -> None:
    for attractor in list_attractors(cwd):
        if attractor.status == "active":
            attractor.status = "inactive"
            save_attractor(attractor, cwd=cwd, write_doc=True)


def create_attractor(
    *,
    attractor_id: str,
    title: str,
    version: str,
    path: str,
    intent: str,
    owner: str = "architecture",
    invariants: list[str] | None = None,
    status: str = "active",
    supersedes: str = "none",
    reason: str = "",
    impact: str = "",
    migration_strategy: str = "",
    cwd: Path | None = None,
) -> AttractorRecord:
    ensure_workspace(cwd)
    validate_identifier(attractor_id, "attractor id")
    if status not in {"active", "inactive"}:
        raise AbhError(f"invalid attractor status: {status}")
    if attractor_json_path(attractor_id, cwd).exists():
        raise AbhError(f"attractor already exists: {attractor_id}")
    if status == "active":
        deactivate_active_attractors(cwd)
    doc_path = path or str(attractor_doc_path(attractor_id, cwd))
    should_write_doc = not Path(doc_path).exists()
    attractor = AttractorRecord(
        id=attractor_id,
        title=title,
        version=version,
        status=status,
        path=doc_path,
        owner=owner,
        supersedes=supersedes,
        reason=reason,
        impact=impact,
        migration_strategy=migration_strategy,
        intent=intent,
        invariants=list(invariants or []),
        doc_path=doc_path,
    )
    return save_attractor(attractor, cwd=cwd, write_doc=should_write_doc)


def supersede_attractor(
    *,
    old_id: str,
    new_id: str,
    title: str,
    version: str,
    path: str,
    reason: str,
    impact: str,
    migration_strategy: str,
    owner: str = "architecture",
    intent: str | None = None,
    invariants: list[str] | None = None,
    cwd: Path | None = None,
) -> tuple[AttractorRecord, AttractorRecord]:
    old = load_attractor(old_id, cwd)
    old.status = "inactive"
    save_attractor(old, cwd=cwd, write_doc=True)
    new = create_attractor(
        attractor_id=new_id,
        title=title,
        version=version,
        path=path,
        intent=intent or old.intent,
        owner=owner,
        invariants=invariants if invariants is not None else list(old.invariants),
        status="active",
        supersedes=old.id,
        reason=reason,
        impact=impact,
        migration_strategy=migration_strategy,
        cwd=cwd,
    )
    return old, new


def is_active_attractor_reference(value: str, cwd: Path | None = None) -> bool:
    try:
        active = active_attractor(cwd)
    except AbhError:
        return Path(value).exists()
    return value == active.id or value == active.path


def render_attractor_markdown(attractor: AttractorRecord) -> str:
    def bullet_lines(values: list[str]) -> str:
        if not values:
            return "-"
        return "\n".join(f"- {value}" for value in values)

    return (
        f"# Attractor: {attractor.title}\n\n"
        "## Metadata\n\n"
        f"- ID: {attractor.id}\n"
        f"- Version: {attractor.version}\n"
        f"- Status: {attractor.status}\n"
        "- Scope: repo\n"
        f"- Owner: {attractor.owner}\n"
        f"- Supersedes: {attractor.supersedes}\n\n"
        "## Intent\n\n"
        f"{attractor.intent}\n\n"
        "## Invariants\n\n"
        f"{bullet_lines(attractor.invariants)}\n\n"
        "## Change Record\n\n"
        f"- Reason: {attractor.reason or 'initial registration'}\n"
        f"- Impact: {attractor.impact or 'none'}\n"
        f"- Migration Strategy: {attractor.migration_strategy or 'none'}\n"
    )


def seed_active_attractor_from_document(cwd: Path | None = None) -> AttractorRecord | None:
    if list_attractors(cwd):
        return None
    default_doc = docs_attractors_dir(cwd) / "abh-core-attractor.md"
    if not default_doc.exists():
        return None
    return create_attractor(
        attractor_id="attractor-abh-core",
        title="ABH Core",
        version="0.1.0",
        path=str(default_doc.relative_to(Path.cwd() if cwd is None else Path(cwd))),
        owner="architecture",
        intent="Attractor Before Harness 的核心结构必须收敛到一个 Git-native、证据优先、生成与验收分离的轨迹控制框架。",
        invariants=["每个可执行 plan 必须绑定一个 active attractor。"],
        cwd=cwd,
    )
