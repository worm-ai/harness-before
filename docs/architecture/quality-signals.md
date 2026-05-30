# ABH Quality Signals

## Purpose

Quality signals are the Stage 6 vocabulary for answering three questions:

- Where is the project drifting?
- Which past experience is reusable now?
- What is the current project health posture?

Stage 6 is product-quality-first and agent-navigation-second. ABH should first make quality problems visible with local, inspectable evidence. Agent navigation can then consume those signals to recommend the next useful action.

## Signal Shape

Every quality signal should be machine-readable and evidence-backed.

Minimum shared fields:

- `id`: stable identifier within its producing object.
- `kind`: signal family, such as `drift`, `memory`, `verification`, `audit`, or `health`.
- `severity`: `info`, `low`, `medium`, `high`, or `critical`.
- `confidence`: `low`, `medium`, or `high`.
- `status`: `active`, `resolved`, `superseded`, or `dismissed`.
- `summary`: concise human-readable statement.
- `evidence_refs`: file paths, object ids, or artifact ids that support the signal.
- `source_excerpt`: short source text excerpt when the signal comes from text evidence.
- `matched_span`: optional start/end offsets or line references for text-derived findings.
- `related_plan_ids`: plan ids connected to the signal.
- `related_audit_ids`: audit ids connected to the signal.
- `related_memory_ids`: memory ids connected to the signal.
- `related_drift_ids`: drift report ids connected to the signal.
- `recommendation`: the next inspection or mitigation action.
- `first_seen` and `last_seen`: timestamps when ABH can determine them.

Existing objects may not have all fields at first. Readers must treat missing fields as unknown rather than invalid so historical records remain usable.

## Severity

Severity describes product-quality impact, not implementation difficulty.

- `critical`: likely invalidates a plan, release, or core ABH invariant.
- `high`: likely causes wrong agent behavior, false closure confidence, or repeated serious drift.
- `medium`: likely creates avoidable rework or hides meaningful evidence.
- `low`: local quality issue with limited blast radius.
- `info`: useful context, weak risk, or successful quality evidence.

Stage 6 reports should rank unresolved `critical` and `high` signals above workflow convenience items.

## Confidence

Confidence describes how strongly local evidence supports the signal.

- `high`: direct match against plan non-goals, active attractor, doctor output, verification metadata, or audit verdicts.
- `medium`: rule-based or relationship-based inference with clear supporting evidence.
- `low`: weak keyword match, incomplete evidence, or signal that needs human review.

Confidence is not a probability. It is an evidence-quality label for local ABH records.

## Drift Signals

Drift findings should answer: where did project behavior, documentation, or implementation diverge from the declared trajectory?

Future drift findings should include:

- rule id and rule family;
- severity and confidence;
- matched span and source excerpt;
- evidence path or object id;
- related plan id when a non-goal, exit criterion, or attractor invariant is involved;
- recommendation.

Drift analysis remains local and rule-based in Stage 6. ABH should not call an LLM or external service to score drift.

## Memory Signals

Memory entries become reusable quality knowledge when they can say when to use them and whether they are still valid.

Memory Index records the first runtime layer of this metadata:

- tags;
- status;
- related plans, audits, and drift reports;
- superseded_by for outdated learning;
- reuse guidance through summary, context, implication, evidence, and relationship fields explaining when the memory should influence a plan, route, audit, or next action.

Memory search still supports keyword lookup, and Stage 6 makes relationship and status filters first-class through `--status`, `--tag`, `--related-plan`, `--related-audit`, and `--related-drift`. Historical memory records remain readable; missing metadata is treated as active memory with empty tags and relationship lists.

## Verification And Audit Signals

Verification and audit records already contain important quality signals:

- verification result, trust level, stale flag, and stale reasons;
- failure classifications;
- audit result, independence, auditor context, verification basis, findings, and follow-ups.

Stage 6 health reporting should consume these existing fields before inventing new ones.

## Health Aggregation

Project health is not one score in Stage 6. It is a structured summary:

- current posture: `healthy`, `watch`, `at_risk`, or `blocked`;
- top unresolved quality risks;
- plan flow metrics, such as open count and close rate;
- verification metrics, such as stale latest verification count and failure classifications;
- audit metrics, such as pass/fail/need_info counts and repeated findings;
- drift metrics, such as active high-severity drift and repeated drift families;
- memory metrics, such as reusable active memories and superseded memories still being referenced;
- recommended inspections for humans and agents.

The health report should degrade gracefully. If drift or memory metadata is not available yet, it should report missing signal depth instead of pretending the project is healthy.

## Agent Navigation

`abh next --json` should remain conservative. It should not replace human judgment or audit decisions.

After Stage 6 reporting exists, agent navigation may use quality signals to recommend inspections such as:

- inspect high-severity active drift before materializing new roadmap work;
- refresh stale verification before requesting audit;
- read reusable memories related to the current plan;
- review repeated audit findings before closing a plan.

The default posture is B-first, C-second: product quality signals are produced for humans first, then reused by agents for safer navigation.
