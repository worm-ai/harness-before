# Audit: plan-010-core-governance-hardening

## Metadata

- Audit ID: audit-010-core-governance-hardening
- Plan: plan-010-core-governance-hardening
- Auditor: independent-auditor
- Status: complete
- Created: 2026-05-23T13:38:40.129849+00:00
- Updated: 2026-05-23T13:38:56.885724+00:00

## Scope

检查 plan-010 是否完成阶段 1 内核治理硬化：清理 demo 状态噪音、加入 schema_version、建立 CI、明确版本策略、同步当前状态文档

## Evidence Reviewed

- docs/plans/plan-010-core-governance-hardening.md
- README.md
- docs/development-roadmap.md
- docs/task-board.md
- .github/workflows/ci.yml
- abh/models.py
- tests/test_cli.py
- docs/memory/mem-post-close-doc-sync-001.md

## Findings

| Severity | Finding | Evidence | Recommendation |
| --- | --- | --- | --- |
| Low | CI workflow 未显式执行 pip install -e . | .github/workflows/ci.yml 直接从 checkout 后运行 abh 命令 | 后续可加入 python3 -m pip install -e . 以提高 CI 路径可靠性 |
| Low | plan-010 的 Audit 字段在审计记录前为空 | docs/plans/plan-010-core-governance-hardening.md | 记录本次 audit 后会自动写入 plan 文档 |
| Info | abh plan list 显示 plan-010 仍为 ready 状态 | abh plan list 输出 | 审计通过后执行 close 关闭计划 |
| Info | 存在未跟踪的实施计划辅助文件 | docs/superpowers/plans/2026-05-23-core-governance-hardening.md | 确认纳入仓库作为实施记录 |
| Info | 所有变更尚未提交到 git | git status | 关闭后统一检查变更状态并由用户决定提交 |

## Verdict

- Result: pass
- Rationale: Plan-010 的 5 条 exit criteria 全部满足：plan-200-demo 已从 plan list 和 docs/.abh 对应记录中清除且 doctor 返回 ok；schema_version 覆盖 PlanRecord、VerificationRun、AuditRecord、MemoryRecord、DriftReport、DriftFinding 的 to_dict 并保持旧 JSON 兼容；CI workflow 覆盖 unittest、abh doctor、abh --help、abh plan list；README 明确 pyproject.toml [project].version 与 abh.__version__ 必须一致；roadmap/task-board 已体现 Sprint 10 和 plan-010。Non-goals 均遵守，17 个测试全部通过。

## Follow-Ups

- CI 中考虑加入 python3 -m pip install -e .
- 在 abh doctor 中增加 schema version 不一致检测
- 启动 plan-011-verify-runner
