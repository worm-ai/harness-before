# Source of Truth

This file defines ABH source-of-truth precedence. It answers which artifact should be trusted for each question type and how conflicts are resolved.

## Core Rule

Repository files are the truth surface, but no single file answers every question. Choose the owner doc or executable artifact by question type.

## Precedence by Question

| Question | Primary truth source | Secondary evidence | Conflict rule |
| --- | --- | --- | --- |
| What should ABH converge toward? | Active attractor | architecture docs, audits | If a plan conflicts with the active attractor, update the plan or supersede the attractor through an explicit attractor change. |
| What should this slice deliver? | Plan goals, non-goals, exit criteria | roadmap queue item, user request | If roadmap and plan disagree after materialization, the plan controls the slice and roadmap must be updated. |
| What is the current implementation? | Code and tests | README, architecture docs | If docs and code disagree, treat it as implementation drift or stale docs; do not silently choose one. |
| What is the command contract? | `abh/commands.py` and JSON/MCP tests | `docs/architecture/agent-protocol.md` | If protocol docs and command metadata disagree, update docs or contract in the plan that owns the change. |
| What validation actually ran? | `.abh/verifications/*.json` | plan validation checklist, CI logs | A passing verification proves command execution only; audit decides whether it covers exit criteria. |
| Is a plan complete? | Passing independent audit plus plan closure evidence | verification records, code, docs | Verification pass alone is never completion. |
| What should future Agents remember? | Active memory records | audits, drift reports, plans | Memory records should preserve reusable failure knowledge, not ordinary progress logs. |
| What should be built next? | `.abh/roadmap.json` queue | development roadmap, task board | Queue keys are stable future intent; concrete `plan-NNN-*` ids only exist after materialization. |

## Conflict Resolution

- Requirements and design disagree: decide whether the baseline changes, then update the owner docs in the same plan.
- Design and architecture disagree: decide whether it is product behavior or technical structure; update `docs/design/` or `docs/architecture/` accordingly.
- Code and documentation disagree: classify as implementation drift or stale documentation before closing the plan.
- Plan and verification disagree: update the plan validation checklist or rerun verification; do not reinterpret a failed check as success.
- Audit and implementation claim disagree: audit wins for closure, but findings must cite repository evidence.
- Memory and current facts disagree: deprecate or supersede the memory record; do not delete historical evidence casually.

## Future AGE Layers

`abh init` should seed these source layers in new repositories:

- `docs/context/` for Agent-readable repository context and precedence
- `docs/requirements/` for implementation-ready requirements
- `docs/design/` for application behavior and workflow design
- `docs/architecture/` for technical structure and attractors
