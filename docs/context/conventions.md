# ABH Conventions

## Planning

- Future work starts as a stable key in `.abh/roadmap.json`.
- Concrete `plan-NNN-*` ids are assigned only by `abh roadmap materialize <key>`.
- A plan may enter `ready` only when it references the current active attractor and has enough goals, non-goals, exit criteria, validation checks, and closure evidence.
- Once a plan exists, it must close through verification evidence and independent audit.

## Verification

- `abh verify run <plan-id>` executes the plan validation checklist and records local shell evidence.
- `trust_level` describes where evidence came from; it does not prove functional completeness.
- Stale verification is a risk signal for audit and closure decisions.

## Audit

- Audit is the completion decision layer.
- Audit findings must cite files, commands, records, or other repository evidence.
- The implementation session should not treat its own completion claim as audit evidence.

## Memory

- Memory records preserve reusable lessons: false assumptions, rejected paths, divergent patterns, and overturned completion judgments.
- Ordinary status updates belong in plans, audits, verifications, task-board entries, or future logs, not memory.

## Documentation

- Stable owner docs describe durable context, requirements, design, and architecture.
- Plans, audits, drift reports, and memory are control records for specific changes or reusable history.
- Avoid embedding one-off analysis reports into stable owner docs when a plan, audit, memory, or analysis file would be more precise.
