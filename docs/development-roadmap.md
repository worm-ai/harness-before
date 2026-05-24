# Attractor Before Harness 开发排期

## 1. 文档定位

本文档是项目的主排期基线，负责同时承载两条线：

- 历史执行线：记录已经交付并审计关闭的 Sprint 和 plan。
- 长期阶段线：按照 `docs/阶段规划.md` 的七阶段路线，规划后续 12 个月演进。

当两条线发生冲突时，已关闭 plan 和 audit 是历史事实来源；长期阶段线是未来排期来源。新的 plan 应优先从长期阶段线中切出最小可关闭范围。

## 1.1 术语说明

- Sprint：时间盒或阶段性工作批次，用于描述项目推进节奏。
- Plan：ABH 中可验证、可审计、可关闭的最小工作单元。
- Sprint 编号和 plan 编号不要求一一对应。一个 Sprint 可以包含多个 plan，例如 Sprint 7 同时包含 `plan-007-sprint-7-dogfood` 和 `plan-007-zero-dep-install`；一个长期阶段也可以跨多个 Sprint 和 plan。
- 从 Sprint 12 开始，建议 plan ID 按全局递增编号命名，避免把 Sprint 编号误认为 plan 编号。

## 2. 排期假设

- 采用两周一个 Sprint。
- 初期继续保持 Git-native、本地优先、零外部数据库。
- 不急于建设 Web UI，先让 CLI 和 Agent 协议稳定。
- 所有关键对象先落在仓库文件中，并通过 `abh doctor` 防止 `.abh/` 与 `docs/` 分裂。
- 每个阶段都必须能被 plan、verification、audit 和 memory 闭环承接。

## 3. 历史执行线

本节记录已经完成并审计关闭的历史事实。若本节与当前计划状态不一致，以 `.abh/` 中已关闭 plan 和对应 audit 为准。

### v0.1：文档与模型基线

周期：Sprint 1

目标：

- 建立正式目录结构。
- 建立 Attractor、Plan、Audit、Memory 模板。
- 建立第一个项目吸引子。
- 建立第一份启动计划。
- 固定验收规则和状态流转。

状态：已完成，对应 `plan-001-sprint-1-foundation`。

### v0.2：本地计划闭环

周期：Sprint 2

目标：

- 实现计划创建和状态流转。
- 实现本地验证结果记录。
- 支持计划绑定吸引子。
- 支持 closure evidence 收集。

状态：已完成，对应 `plan-002-sprint-2-local-plan-loop`。

### v0.3：独立审计与记忆

周期：Sprint 3

目标：

- 实现审计记录流程。
- 实现 memory 记录和检索。
- 强制关闭前审计。
- 支持假完成和证据不足记录。

状态：已完成，对应 `plan-003-sprint-3-audit-memory-close`。

### v0.4：路由与漂移分析

周期：Sprint 4

目标：

- 实现问题路由建议。
- 实现基础漂移分类。
- 把漂移发现反向写入计划和 memory。

状态：已完成，对应 `plan-004-sprint-4-route-drift`。

### v0.5：运行说明与自举稳定

周期：Sprint 5-7

目标：

- 明确 Python、pip、uvx 和 uv tool install 的运行路径。
- 将历史手写计划迁移到 abh CLI 双写数据。
- 新增 plan / memory / audit list 查询能力。
- 增强 route 和 drift，使其能利用当前计划状态和计划 non-goals。
- 通过 dogfooding 记录文档同步、独立审计和安装门槛相关 memory。

状态：已完成，对应 `plan-005-runtime-docs-install`、`plan-006-stabilize`、`plan-007-sprint-7-dogfood`、`plan-007-zero-dep-install`。

### v0.6：路线同步与一致性检查

周期：Sprint 8

目标：

- 将 roadmap 和 task-board 同步到当前实际进度。
- 新增 `abh doctor`，检查 `.abh/` JSON 与 `docs/` Markdown 是否一致。
- 将文档/运行态一致性纳入 plan 关闭前验证。
- 为 doctor 命令补充测试覆盖。

状态：已完成，对应 `plan-008-roadmap-sync-and-doctor`。

### v0.7：长期阶段路线对齐

周期：Sprint 9

目标：

- 将本路线图改为“历史执行线 + 长期阶段线”的双层结构。
- 严格承接 `docs/阶段规划.md` 的阶段 1-7 长期路线。
- 明确 Sprint 1-8 与长期阶段的映射关系。
- 列出下一批推荐计划，作为后续 plan 切分入口。

状态：已完成，对应 `plan-009-roadmap-phase-alignment`。

### v0.8：内核治理硬化

周期：Sprint 10

目标：

- 清理 `plan-200-demo` 遗留 draft 状态噪音。
- 为核心 JSON 对象加入 `schema_version`。
- 建立 CI 基础门禁。
- 明确包版本和 README 功能版本之间的关系。
- 把关闭后文档同步检查纳入治理门禁。

状态：已完成，对应 `plan-010-core-governance-hardening`。

### v0.9：阶段 1 治理收尾

周期：Sprint 11

目标：

- 迁移历史 `.abh` JSON 对象补齐 `schema_version`。
- 增强 `abh doctor`，检查缺失 `schema_version` 的核心 JSON 对象。
- 在 CI 中补齐 editable install 路径。
- 标记阶段 1 完成，并把下一轮路线推进到阶段 2。

状态：已完成，对应 `plan-011-stage-1-finalization`。

### v0.10：Agent Protocol 基线

周期：Sprint 12

目标：

- 将 Agent Protocol 插入阶段 1 和原验证执行器阶段之间，明确它是 CLI 走向 Agent 工具协议的必经中间层。
- 定义 JSON CLI Contract、Structured Error、Agent Tool Schema、Read-only MCP 和 Controlled Write MCP 五层协议基线。
- 同步阶段规划、roadmap 和 task-board，把阶段 2 改为 Agent Protocol Foundation。
- 明确 MCP 写操作、verify runner 和 Attractor Registry 不属于当前计划范围。

状态：已完成，对应 `plan-012-agent-protocol-foundation`。

### v0.11：JSON 输出与结构化错误

周期：Sprint 12

目标：

- 为核心只读命令增加显式 `--json` 输出模式。
- 统一成功响应的 JSON envelope，包含 `schema_version`、`ok`、`command`、`data`、`errors` 和 `warnings`。
- 在 `--json` 模式下为 ABH 业务错误输出结构化 error，同时保留既有返回码。
- 保留默认人类可读输出，不把 JSON 变成默认体验。

状态：已完成，对应 `plan-013-json-output-and-errors`。

### v0.12：只读 MCP Server

周期：Sprint 12

目标：

- 提供 `python3 -m abh.mcp_server` stdio JSON-RPC 入口。
- 暴露 plan、audit、memory、route、doctor 和 drift report 的只读 MCP 工具。
- 返回 MCP tool result，包含 text content 和 `structuredContent`。
- 对未知工具、非法 JSON、缺失对象和 doctor issues 返回结构化错误。

状态：已完成，对应 `plan-014-readonly-mcp-server`。

### v0.13：受控 MCP 写工具

周期：Sprint 12

目标：

- 在只读 MCP 稳定后开放受控写工具。
- 覆盖 plan create/transition、verify record、audit request/record、close、memory add 和 drift analyze。
- 每个写工具必须显式要求 `confirm=true`，缺失确认时返回结构化业务错误且不写入仓库。
- 写工具必须复用 `core.py` 现有函数，保留状态机、验证、审计关闭和 doctor 规则。

状态：已完成，对应 `plan-015-controlled-mcp-write-tools`。

### v0.14：Verify Runner MVP

周期：Sprint 13

目标：

- 新增 `abh verify run <plan>`，执行计划 validation checklist 中的本地命令。
- 保存 stdout/stderr 摘要、退出码、耗时和 artifact。
- 成功时记录 pass verification，失败或超时时记录 fail verification。
- 失败时复用现有验证记录规则，阻断 ready/running plan。
- 支持 `verify run --json`，保留机器可读 envelope。
- 记录 runner 递归自调用风险 memory。

状态：已完成，对应 `plan-016-verify-runner`。

### v0.15：Plan Update MVP

周期：Sprint 13

目标：

- 新增 `abh plan update <plan_id>`，支持通过 CLI 追加计划内容。
- 支持追加 goals、non-goals、exit criteria、validation checklist 和 closure evidence。
- 保持 `.abh/plans` JSON 与 `docs/plans` Markdown 双写一致。
- 重复追加同一内容时自动去重。
- 提供精确的 `--remove-validation` 修复路径，用于移除不安全或过期的 validation checklist 条目。
- 记录 plan update dogfood 中发现的递归验证事故和修复记忆。

状态：已完成，对应 `plan-017-plan-update`。

### v0.16：Core Module Split

周期：Sprint 14

目标：

- 在不改变 CLI、MCP、JSON schema 或 Markdown 输出行为的前提下，将 `core.py` 中稳定的 plan、audit 和 verification 逻辑拆分到更小的领域模块。
- 新增 `abh/plans.py`、`abh/audits.py`、`abh/verifications.py` 和 `abh/errors.py`，降低核心模块继续膨胀的维护风险。
- 保持 `abh.core` 兼容导出，确保既有 CLI、MCP 和外部导入路径不回归。
- 补充 core re-export 边界测试，并通过 verification 与独立审计关闭。

状态：已完成，对应 `plan-018-core-module-split`。

## 4. 当前执行焦点

Sprint 21 已完成。`plan-025-stage-3-finalization` 已关闭，阶段 3 功能队列收束为 v0.3 Verify Runner 里程碑；下一阶段启动方向是阶段 4 Attractor Registry。

`plan-015-controlled-mcp-write-tools` 已关闭。阶段 2 Agent Protocol Foundation 已完整完成：核心只读命令具备显式 JSON 输出和结构化错误格式，MCP stdio Server 同时提供只读工具和受控写工具，写工具必须显式 `confirm=true` 并复用现有 ABH 门禁。

当前执行计划：暂无。下一条计划建议为 `plan-026-attractor-registry`。

当前阶段状态：

- 已完成：`plan-012-agent-protocol-foundation`、`plan-013-json-output-and-errors`。
- 已完成：`plan-014-readonly-mcp-server`。
- 已完成：`plan-015-controlled-mcp-write-tools`。
- 阶段 2 判定：完成。JSON contract、结构化错误、只读 MCP 和受控 MCP 写工具均已通过 verification 与独立审计。
- 当前里程碑：v0.3 Verify Runner 阶段功能队列已交付；`plan-016-verify-runner`、`plan-017-plan-update`、`plan-018-core-module-split`、`plan-019-verification-environment-metadata`、`plan-020-stage-3-functional-plan`、`plan-021-verification-trust-and-stale-detection`、`plan-022-verification-failure-classification`、`plan-023-atomic-abh-writes` 和 `plan-024-memory-drift-routing-module-split` 已完成。
- 当前阶段：阶段 3 验证执行器已经具备 v0.3 所需能力，`plan-025-stage-3-finalization` 已留下收尾验证、独立审计和阶段 4 启动证据。
- 当前阶段 3 判定：完成。v0.3 Verify Runner 里程碑已关闭。
- 下一阶段焦点：阶段 4 Attractor Registry，预计从 `plan-026-attractor-registry` 启动。

## 5. 长期阶段线

### 阶段 1：恢复权威基线，稳住内核

周期：1 个月

目标：让项目自身不再漂移。

核心事项：

- 更新 `docs/development-roadmap.md` 和 `docs/task-board.md`，把 Sprint 6/7、零门槛安装和 Sprint 8 纳入正式路线。
- 建立 `abh doctor`，检查 `.abh/*.json` 与 `docs/*.md` 是否一致。
- 清理或关闭遗留 draft 计划，尤其是 `plan-200-demo`，降低状态噪音。
- 给数据对象加 schema/version 字段，为后续迁移做准备。
- 建立 CI：运行 `python3 -m unittest tests/test_cli.py -v`，并验证 `python3 -m abh --help`、`python3 -m abh plan list`、`python3 -m abh doctor`。
- 把版本号从当前 `0.1.0` 进入可解释的发布节奏，避免 README 功能与包版本脱节。

当前状态：

- 已完成：Sprint 6/7/8 纳入路线、`abh doctor` 第一版、路线图和看板同步、清理 `plan-200-demo`、新对象 schema version、历史 JSON schema 迁移、CI 基础门禁、editable install CI 路径、版本策略说明。
- 阶段 1 判定：完成。阶段 1 的必需治理门禁已经具备，可以进入阶段 2。
- 延期项：更深的内容级 doctor 校验和正式发布自动化，推迟到后续质量/发布计划，不阻塞阶段 2 启动。

### 阶段 2：Agent Protocol 基础

周期：1-2 个月

目标：把 ABH 从“人类可读 CLI”升级为“Agent 可程序化调用的治理接口”。

核心事项：

- 为核心读操作增加机器可解析输出，例如 `--json` 或等价 JSON mode。
- 定义稳定的 Agent tool schema，覆盖 plan、verify、audit、memory、route、drift 和 doctor 的输入、输出和错误格式。
- 统一 CLI 返回码和结构化错误，保证 Agent 能区分成功、校验失败、业务阻断和系统错误。
- 新增只读 MCP Server 第一版，让 Claude、Cursor 等 Agent 能读取计划、审计、记忆、漂移和当前路线。
- MCP 写操作只在读协议和工具 schema 稳定后开放，并继续遵守现有 ABH 门禁。

协议基线：`docs/architecture/agent-protocol.md`。

当前状态：

- 已完成：`plan-012-agent-protocol-foundation` 建立 Agent Protocol 基线、阶段路线和只读 MCP 分阶段策略。
- 已完成：`plan-013-json-output-and-errors` 实现核心只读命令显式 `--json` 输出、统一 JSON envelope 和结构化 ABH 错误输出。
- 已完成：`plan-014-readonly-mcp-server` 已封装只读 MCP stdio Server，暴露 plan、audit、memory、route、doctor 和既有 drift report 的只读工具入口。
- 已完成：`plan-015-controlled-mcp-write-tools` 实现受控 MCP 写工具，并通过验证与独立审计。
- 当前最小闭环：Agent 已经可以通过 CLI 获取可解析 JSON，通过 MCP 读取 ABH 状态，并在显式确认后调用受控写工具。
- 阶段 2 判定：完成。
- 后置项：verify runner 后续增强、Attractor Registry、报告和发布自动化进入后续阶段。

建议版本：v0.2.0，作为阶段 2 里程碑。

计划切分：

- `plan-012-agent-protocol-foundation`（已完成）
- `plan-013-json-output-and-errors`（已完成）
- `plan-014-readonly-mcp-server`（已完成）
- `plan-015-controlled-mcp-write-tools`（已完成）

### 阶段 3：从“记录验证”升级到“执行验证证据”

周期：1-3 个月

目标：让 `verify` 从人工记录结果升级为本地验证执行器，并把验证从“人或 Agent 声称已通过”推进到“ABH 确实执行过命令并留下可复现、可审计的机器证据”。

可信边界：

- `verify run` 只能证明某个时间、某个 git 状态、某个本地环境下执行过指定命令，并记录了返回结果。
- `verify run` 不证明功能绝对正确，不保证测试覆盖充分，也不提供防篡改证明。
- 独立审计仍需判断验证命令是否真实覆盖 exit criteria，不能只因为 verification 为 pass 就关闭 plan。

核心事项：

- 新增 `abh verify run <plan>`，按 plan 的 validation checklist 执行命令。
- 保存 stdout/stderr 摘要、退出码、耗时和 artifact。
- 记录 git commit、dirty status、cwd、ABH 版本、Python 版本、命令 argv、timeout 和环境变量 allowlist。
- 为 verification 标注可信等级，例如人工记录、本地执行、隔离目录执行和 CI 执行。
- 失败时生成可审计证据；是否自动把 plan 转入 `blocked` 需要区分验证失败、环境失败、网络失败和 flaky failure。
- 当 validation checklist、plan 内容或 git 状态变化后，旧 verification 应能被识别为可能 stale。
- 支持 `abh plan update`，补充 goals、non-goals、exit criteria、validation checklist 和 closure evidence。
- 在不破坏现有 CLI 的前提下，逐步拆分 `core.py` 为更小的领域模块，例如 `plans.py`、`audits.py`、`memory.py`、`drift.py`、`routing.py`。

当前状态：

- 已完成：`plan-016-verify-runner` 交付 `abh verify run <plan>` MVP，能够执行 validation checklist、记录 stdout/stderr 摘要、退出码、耗时和 artifact，并在失败时阻断 ready/running plan。
- 已完成：`plan-017-plan-update` 交付 `abh plan update <plan>`，支持追加计划字段、去重、JSON/Markdown 双写，以及通过 `--remove-validation` 精确修复错误 validation checklist。
- 已完成：`plan-018-core-module-split` 将 plan、audit、verification 和 shared errors 逻辑拆分到领域模块，并通过 `abh.core` 保持现有导入兼容。
- 已完成：`plan-019-verification-environment-metadata` 为 `verify run` 记录补充结构化 environment 元数据，并保持旧 verification 记录可读取。
- 已完成：`plan-020-stage-3-functional-plan` 将阶段 3 剩余功能规划成可执行 plan 队列。
- 已完成：`plan-021-verification-trust-and-stale-detection` 为 verification 补充 trust_level，并在 `plan status --json` 暴露 latest verification stale 摘要。
- 已完成：`plan-022-verification-failure-classification` 为失败的 `verify run` 补充结构化 `failure_classifications`。
- 已记录：plan-017 dogfood 中的递归验证风暴已压缩保留 7 条代表性 verification 作为证据，重复超时记录未继续保留。
- 已记录：plan-019 dogfood 中发现 ABH 对同一对象并行写入会损坏 JSON/Markdown，后续应补原子写或文件锁保护。
- 已完成：`plan-023-atomic-abh-writes` 为 `.abh` JSON 和 Markdown 保存路径补充原子写与本地文件锁。
- 已完成：`plan-024-memory-drift-routing-module-split` 将 memory、drift 和 routing 行为从 `core.py` 拆到领域模块。
- 已完成：`plan-025-stage-3-finalization` 将阶段 3/v0.3 标记为完成，并同步阶段 4 启动条件。

建议版本：v0.3。

建议后续计划：

- `plan-016-verify-runner`（已完成）
- `plan-017-plan-update`（已完成）
- `plan-018-core-module-split`（已完成）
- `plan-019-verification-environment-metadata`（已完成）
- `plan-020-stage-3-functional-plan`（已完成）
- `plan-021-verification-trust-and-stale-detection`（已完成）
- `plan-022-verification-failure-classification`（已完成）
- `plan-023-atomic-abh-writes`（已完成）
- `plan-024-memory-drift-routing-module-split`（已完成）
- `plan-025-stage-3-finalization`（已完成）

### 阶段 4：补齐 Attractor Registry

周期：3-4 个月

目标：把吸引子从文档约定升级为 CLI 可管理的一等对象。

核心事项：

- 新增 `abh attractor list/show/create/supersede`。
- plan 进入 `ready` 前校验引用的是 active attractor。
- 记录吸引子版本差异、升级原因、影响范围和迁移策略。
- route/drift 优先读取 active attractor，而不是只靠固定路径和关键词。

建议版本：v0.4。

建议后续计划：

- `plan-026-attractor-registry`
- `plan-027-attractor-aware-route-drift`

### 阶段 5：真正独立审计

周期：4-6 个月

目标：让“独立审计”从流程原则升级为工具支持。

核心事项：

- 新增 `abh audit prompt <plan>`，生成独立审计提示词。
- 新增 `abh audit bundle <plan>`，打包审计所需证据清单。
- `abh audit record` 增加 auditor context/source 字段。
- 关闭计划时检查是否有 fresh/independent 标记的通过审计。
- 固化审计模板，避免每次靠人工记忆。

建议版本：v0.5。

建议后续计划：

- `plan-028-audit-prompt-bundle`
- `plan-029-independent-audit-gate`

### 阶段 6：漂移与记忆质量提升

周期：6-9 个月

目标：降低 drift 误报/漏报，让 memory 从列表检索升级为可复用轨迹知识。

核心事项：

- drift finding 增加 severity、matched span、source excerpt 和 confidence。
- memory 支持标签、状态废弃、related plan/audit 反向索引。
- route 从关键词匹配升级为“对象图 + 简单权重排序”。
- 新增 `abh report`，展示计划关闭率、审计驳回率、重复漂移率和 memory 命中情况。

建议版本：v0.6。

建议后续计划：

- `plan-030-drift-quality`
- `plan-031-memory-index`
- `plan-032-reporting`

### 阶段 7：团队可用与生态集成

周期：9-12 个月

目标：让 ABH 成为任何仓库都能接入的本地优先治理层。

核心事项：

- 新增 `abh init`，一键初始化任意仓库。
- 提供 GitHub Actions 模板：PR 中自动跑 `abh doctor`、测试和漂移检查。
- 提供 Git hooks 可选集成：关闭 plan 前检查审计和证据链。
- 支持多仓库共享 attractor/memory 的导入导出。
- 发布到 PyPI，同时保留 `uvx --from git+...` 路径。

建议版本：v1.0。

建议后续计划：

- `plan-033-init-and-ci-templates`
- `plan-034-multi-repo-sharing`
- `plan-035-pypi-release`

## 6. 历史执行线与长期阶段映射

| 长期阶段 | 已完成历史计划 | 已完成内容 | 剩余内容 |
| --- | --- | --- | --- |
| 阶段 1：恢复权威基线，稳住内核 | `plan-006-stabilize`, `plan-007-zero-dep-install`, `plan-008-roadmap-sync-and-doctor`, `plan-009-roadmap-phase-alignment`, `plan-010-core-governance-hardening`, `plan-011-stage-1-finalization` | 历史计划迁移、安装门槛降低、`abh doctor`、路线图对齐、demo 清理、schema version、历史 schema 迁移、CI、版本策略 | 已完成；内容级 doctor、发布自动化转入后续质量/发布计划 |
| 阶段 2：Agent Protocol 基础 | `plan-012-agent-protocol-foundation`, `plan-013-json-output-and-errors`, `plan-014-readonly-mcp-server`, `plan-015-controlled-mcp-write-tools` | Agent Protocol 五层基线、阶段路线、核心只读命令 `--json`、统一 JSON envelope、结构化 ABH 错误、只读 MCP stdio Server、受控 MCP 写工具 | 已完成；verify runner 和 Attractor Registry 转入后续阶段 |
| 阶段 3：验证执行器 | `plan-002-sprint-2-local-plan-loop`, `plan-016-verify-runner`, `plan-017-plan-update`, `plan-018-core-module-split`, `plan-019-verification-environment-metadata`, `plan-020-stage-3-functional-plan`, `plan-021-verification-trust-and-stale-detection`, `plan-022-verification-failure-classification`, `plan-023-atomic-abh-writes`, `plan-024-memory-drift-routing-module-split`, `plan-025-stage-3-finalization` | `verify record` 可记录验证结果；`verify run` 可执行 validation checklist、记录机器证据、失败阻断计划并支持 JSON 输出；`plan update` 可通过 CLI 双写追加计划字段并精确修复 validation checklist；`core.py` 已拆出 plan/audit/verification/errors/memory/drift/routing 领域模块并保持兼容导出；environment 元数据已补充 cwd、git、版本、timeout、argv 和 allowlisted env 证据；trust level、stale summary 和失败分类已落盘并暴露给审计；`.abh` JSON 与 Markdown 保存路径已补充原子写和本地文件锁；阶段 3 已通过 `plan-025` 收尾为 v0.3 Verify Runner 里程碑 | 已完成；Attractor Registry 转入阶段 4 |
| 阶段 4：Attractor Registry | `plan-001-sprint-1-foundation` | active attractor 文档和模板 | attractor CLI、版本迁移、active 校验 |
| 阶段 5：真正独立审计 | `plan-003-sprint-3-audit-memory-close`, `plan-007-zero-dep-install`, `plan-008-roadmap-sync-and-doctor` | audit request/record/close 闭环，人工独立审计流程已 dogfood | audit prompt/bundle、独立上下文字段、关闭门禁 |
| 阶段 6：漂移与记忆质量提升 | `plan-004-sprint-4-route-drift`, `plan-007-sprint-7-dogfood` | 关键词 drift、route 注入活跃计划和记忆 | severity/confidence、memory 索引、对象图路由、report |
| 阶段 7：团队可用与生态集成 | `plan-007-zero-dep-install` | uvx/uv tool install 降低接入门槛 | init、CI 模板、Git hooks、多仓库、PyPI |

## 7. 下一批推荐计划

本节只列下一批仍可切分执行的计划。已关闭的 `plan-012-agent-protocol-foundation`、`plan-013-json-output-and-errors`、`plan-014-readonly-mcp-server`、`plan-015-controlled-mcp-write-tools` 和阶段 3 的 `plan-016` 至 `plan-025` 已归入第 3 章历史执行线与第 6 章阶段映射；下一条建议计划是 `plan-026-attractor-registry`。

已完成参考：

- `plan-016-verify-runner`：交付 `abh verify run <plan>` MVP，执行 validation checklist 并记录机器验证证据。
- `plan-017-plan-update`：交付 `abh plan update <plan>` MVP，支持计划字段追加、去重、双写同步和 validation checklist 精确修复。
- `plan-018-core-module-split`：拆出 plan/audit/verification/errors 领域模块，并保持 `abh.core` 公共导入兼容。
- `plan-019-verification-environment-metadata`：为 `verify run` 记录补齐环境元信息，为 stale 检测和可信等级提供基础证据。

### plan-019-verification-environment-metadata

状态：已完成，对应 Sprint 15。

范围：

- 在 `verify run` 记录中补齐 git commit、dirty status、cwd、ABH 版本、Python 版本、命令 argv 和 timeout 等环境元信息。
- 保持现有 verification schema 可迁移，旧记录仍可被读取。
- 为后续 stale 检测和可信等级提供证据基础。

不做：

- 不实现隔离执行环境或 CI runner。
- 不改变 pass/fail/partial 语义。
- 不把本地执行结果声明为防篡改证明。

### plan-020-stage-3-functional-plan

状态：已完成，对应 Sprint 16。

范围：

- 将阶段 3 剩余能力拆成具体 plan 队列，明确顺序、边界、非目标和验收重点。
- 同步 roadmap、task-board、README 和阶段规划，避免后续计划 ID 与阶段 4-7 规划冲突。
- 保持 docs-only，不修改 CLI、MCP、schema、verification 语义或模块边界。

不做：

- 不实现可信等级、stale 检测、失败分类、原子写、隔离执行或模块拆分。
- 不改写已关闭计划、审计或验证事实。

### plan-021-verification-trust-and-stale-detection

状态：已完成。

范围：

- 为 verification 记录标注可信等级，例如 `manual_record`、`local_shell`、`ci` 等可扩展枚举。
- 基于 plan validation checklist、plan 更新时间和 git/environment 元数据识别旧 verification 是否可能 stale。
- 在 `plan status --json` 中暴露 latest verification 的 trust/stale 摘要，供 Agent 判断关闭风险。

不做：

- 不实现 CI runner 或隔离执行。
- 不改变现有 pass/fail/partial 结果语义。
- 不让 stale 自动阻断 close；关闭门禁是否升级留给后续独立计划。

### plan-022-verification-failure-classification

状态：已完成。

范围：

- 为 `verify run` 失败增加分类，例如 validation failure、environment failure、timeout、recursive guard、unknown。
- 让 failed checks 的 artifact 更容易审计，区分代码验证失败和执行环境失败。
- 保持 ready/running 失败阻断规则兼容，先只增强证据表达。

不做：

- 不实现 flaky 重试、网络诊断或自动修复。
- 不绕过现有 `record_verification` 状态规则。

### plan-023-atomic-abh-writes

状态：已完成。

范围：

- 针对 dogfood memory `mem-abh-write-concurrency-001`，为 `.abh` JSON 与对应 Markdown 写入增加原子写或文件锁保护。
- 覆盖 plan update、transition、verify run、audit record/close 等同对象连续写入路径。
- 补充并发写入回归测试，避免 JSON/Markdown 尾部重复或截断。

不做：

- 不引入外部数据库或长期后台服务。
- 不改变 ABH 文件格式。

### plan-024-memory-drift-routing-module-split

状态：已完成。

范围：

- 继续 `plan-018` 的模块边界收敛，将 memory、drift 和 routing 行为从 `core.py` 拆到领域模块。
- 保持 `abh.core` 兼容导出和 CLI/MCP 行为不变。
- 补充 re-export 和主要 CLI/MCP 回归测试。

不做：

- 不提升 drift 算法质量。
- 不新增 memory 索引或 route 排序算法。

### plan-025-stage-3-finalization

状态：已完成，对应 Sprint 21。

范围：

- 审核阶段 3 已完成能力是否足以标记 v0.3 里程碑。
- 同步 README、roadmap、task-board、阶段规划，明确阶段 3 完成与阶段 4 启动条件。
- 运行完整验证、doctor 和独立审计，关闭阶段 3。

不做：

- 不新增功能。
- 不替代阶段 4 Attractor Registry 计划。

## 8. 风险控制

- 如果 roadmap、task-board、README 与 `.abh/` 状态不同步，仓库事实来源会再次分裂。
- 如果模板过重，会降低使用率。模板必须短而硬。
- 如果没有 active attractor 校验，后续 plan 仍可能绕过吸引子。
- 如果没有 Agent Protocol，ABH 只能被人类阅读，无法成为 Claude、Cursor 等 Agent 的程序化治理接口。
- 如果 memory 只记录成功结论，会丢失真正有价值的失败轨迹。
- 如果过早做 Web UI，会削弱 CLI 和 Agent 协议这条最关键路径。
