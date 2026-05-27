# ABH Documentation Index

This index routes Agent and maintainer questions to the owner docs that should answer them. It is the first file to read after the active attractor when entering this repository.

## Required Reading Order

1. `docs/architecture/attractors/abh-core-attractor.md` — current active attractor and high-level invariants.
2. `docs/context/project-context.md` — current project purpose, scope, and operating model.
3. `docs/context/source-of-truth.md` — source-of-truth precedence and conflict resolution rules.
4. `docs/context/conventions.md` — repository conventions for plans, verification, audit, memory, and docs.
5. `docs/context/codebase-map.md` — current module map and command surface.
6. `docs/development-roadmap.md` — historical execution line and future roadmap queue discipline.
7. `docs/architecture/agent-protocol.md` — Agent-facing command contract, MCP, and navigation baseline.

## Question Routing

| Question | Primary owner doc | Supporting evidence |
| --- | --- | --- |
| What should ABH converge toward? | `docs/architecture/attractors/abh-core-attractor.md` | `docs/attractor-before-harness-*.md` |
| What is the current project context? | `docs/context/project-context.md` | `README.md`, `docs/development-roadmap.md` |
| Which source wins when docs disagree? | `docs/context/source-of-truth.md` | active attractor, code, tests, plan/audit records |
| How should an Agent behave in this repo? | `docs/architecture/agent-protocol.md` | `docs/context/conventions.md`, `abh/commands.py` |
| What should be built next? | `.abh/roadmap.json` | `docs/development-roadmap.md`, `docs/task-board.md` |
| How should a specific change close? | `docs/plans/<plan-id>.md` | `.abh/plans/<plan-id>.json`, verification records, audit records |
| Did the change really complete? | `docs/audits/<audit-id>.md` | verification artifacts, code, tests, plan exit criteria |
| What failure should future sessions remember? | `docs/memory/<memory-id>.md` | linked plan, audit, verification, or drift evidence |

## AGE Owner-Doc Baseline

ABH adopts the AGE distinction between stable attractors and control mechanisms:

- Stable owner docs: `docs/context/`, `docs/requirements/`, `docs/design/`, `docs/architecture/`.
- Control records: `docs/plans/`, `docs/audits/`, `docs/memory/`, `docs/drift/`, future `docs/logs/`.

Future `abh init`, `abh agent setup`, `abh next`, and `abh onboarding check` should consume this index rather than inventing separate reading-order rules.
