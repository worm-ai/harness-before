# Audit: plan-058-verification-sandbox-and-storage-hardening

## Metadata

- Audit ID: audit-058-dogfood-hardening
- Plan: plan-058-verification-sandbox-and-storage-hardening
- Auditor: human-independent-reviewer
- Auditor Context: unknown
- Independence: independent
- Verification ID: ver-845743bb049a
- Status: complete
- Created: 2026-06-14T09:20:19.714406+00:00
- Updated: 2026-06-14T09:24:51.987817+00:00

## Scope

Independent audit of plan-058: verification execution policy, closed plan immutability, shared read locks, schema v1→v2 migration, unit test modules. Check that all changes are bound to the active attractor invariants, that no non-goals were implemented, and that exit criteria are met.

## Evidence Reviewed

- docs/plans/plan-058-verification-sandbox-and-storage-hardening.md
- abh/verifications.py
- abh/plans.py
- abh/storage.py
- abh/models.py
- abh/core.py
- abh/roadmap.py
- abh/cli.py
- tests/test_verification_policy.py
- tests/test_plans_unit.py
- tests/test_drift_unit.py
- tests/test_storage_concurrency.py

## Semantic Conservation

- Check whether any in-scope commitments disappeared, weakened, or moved to non-authoritative artifacts.
- Distinguish J-flow-only evidence from R-flow evidence that reduces uncertainty through proof, decision, or owner-doc alignment.
- Cite repository evidence for any semantic conservation gap.

## Findings

| Severity | Finding | Evidence | Recommendation |
| --- | --- | --- | --- |
| high | read_json+write_json缺少互斥锁可能导致撕裂读取 | storage.py:271 (write_text仅用file_lock) vs storage.py:29-51 (shared_file_lock用.shared/目录) | 使write_text在写入前等待.shared/目录清空，或让read_json获取共享独占锁 |
| high | file_locks写入者等待循环存在TOCTOU间隙 | storage.py:213-218 | 在获取独占锁后重新检查lock_dir.exists()，最多重试固定次数 |
| medium | check_command_policy可通过双空格绕过rm模式 | verifications.py:48-49 | 匹配前规范化命令：' '.join(lowered.split()) |
| low | migrate_record在schema_version: null时崩溃 | models.py:713 | 添加守卫：if raw is None or raw is False then migrate directly |
| low | VerificationRun.from_dict缺少migrate_record调用 | models.py:248 | 添加data=migrate_record('verification', data)到from_dict |
| low | commitment_phase_state被归类为bookkeeping可在close后修改 | plans.py:20 | 考虑对closed plan保护commitment_phase_state |

## Verdict

- Result: fail
- Rationale: Independent audit found 2 HIGH severity TOCTOU race conditions in file locking (shared_file_lock+write_json lack mutual exclusion; file_locks writer wait has gap). Also found: command policy bypass (double spaces), migrate_record crashes on null schema_version, VerificationRun.from_dict missing migration call, roadmap schema handling gap. Non-goals verified clean. Attractor invariants hold. See audit report for full findings.

## Follow-Ups

- 
