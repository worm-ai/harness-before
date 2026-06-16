# Attractor Before Harness

`Attractor Before Harness` 是一个面向 AI 协作开发的收敛框架与 CLI 工具集。项目核心思想来自"先定义系统要收敛到哪里，再用 harness 持续纠偏"的方法论：先把吸引子、基线、计划、验证、审计和记忆显式化，再让开发过程围绕这些对象运行。

## 零基础使用：不装 Python

适合第一次使用、不了解 Python 环境的用户。你只需要先装 `uv`，它会自动下载和管理 Python；不需要自己安装 Python、pip 或虚拟环境。

### 1. 安装 uv

Windows PowerShell：

```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

macOS / Linux：

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

安装后关闭并重新打开终端。如果想确认是否成功：

```bash
uv --version
```

### 2. 运行或安装 abh

只试用一次：

```bash
uvx --from git+https://github.com/worm-ai/harness-before.git abh --help
```

长期使用，安装到本机命令行：

```bash
uv tool install --from git+https://github.com/worm-ai/harness-before.git abh
abh --help
```

### 3. 在 Codex 里用傻瓜式 skill

如果你是在本仓库里使用 Codex，直接发这句：

```text
Use the skill at `skills/abh-workflow` to manage this repository task through ABH. I am a beginner; tell me only the next safe action and run the ABH checks for me.
```

中文也可以：

```text
使用 `skills/abh-workflow` 这个 skill 帮我处理当前仓库任务。我是小白，只告诉我下一步安全动作，并替我运行 ABH 检查。
```

这个 skill 会引导 Codex 调用 `abh onboarding check --json`、`abh next --json`、`abh doctor --json`、`abh roadmap check --json`，再按需要创建或补齐 plan、运行 verification、生成独立审计提示词、记录审计结果并关闭 plan。你不需要自己写 plan、verification、audit 命令；但独立审计仍必须在单独上下文或由独立 reviewer 完成，不能由同一个实现会话自签。

如果你想让当前仓库默认以 ABH 方式在 Codex 中工作，可以写入仓库级的受管 `.codex/config.toml`：

```bash
abh codex status --json
abh codex on --write --confirm --json
abh codex off --write --confirm --json
```

`abh codex on` 只管理 ABH 写入的 `.codex/config.toml`，不会合并或覆盖用户自写的 unmanaged Codex 配置。

## 项目来源
[Attractor Before Harness: AI 大规模开发的方法论](https://mp.weixin.qq.com/s/TwMkUDLNo2-bIrXrfvPqIw)

这个项目源于对 AI 大规模开发协作方式的整理与工程化尝试，重点解决三个问题：
1. AI 生成结果不稳定，容易偏离长期目标。
2. 单次任务完成不等于系统轨迹正确。
3. 缺少可审计、可回放、可沉淀的开发过程记录。

因此，本项目把"吸引子"作为长期结构基线，把"harness"作为围绕基线运行的控制层，目标是让仓库本身成为事实来源，而不是把判断留在人的临时记忆里。

## 项目功能

当前项目提供一个名为 `abh` 的命令行工具，支持以下能力：

- `plan`：创建、查看、列出和迁移计划状态（6 状态状态机）
- `init`：预览或初始化 ABH workspace，生成 `.abh/`、active attractor 和 AGE owner docs
- `verify`：记录验证命令及其结果
- `audit`：发起、记录和列出独立审计
- `close`：在满足条件后关闭计划
- `memory`：记录、检索和列出外部化记忆
- `route`：根据问题输出建议阅读顺序（含活跃计划和相关记忆）
- `drift`：识别基础漂移并生成漂移报告（支持以计划为基准）
- `attractor`：管理 active attractor，并在 plan ready 前校验吸引子绑定
- `roadmap`：维护稳定 roadmap queue，并在 materialize 时分配真实 plan 编号
- `agent setup`：导出 Codex、Claude Code 和通用 MCP 客户端可读取的只读 setup bundle
- `codex`：预览、启用、停用当前仓库的受管 Codex ABH 配置
- `hooks`：预览或安装本地 ABH pre-commit guardrail hook
- `next`：根据本地 ABH 状态推荐下一条安全动作
- `onboarding check`：检查仓库是否具备 Agent-First ABH readiness 基线
- `report health`：汇总计划、验证、审计、漂移、记忆和 roadmap 信号，生成只读语义压力报告
- `doctor`：检查 `.abh/` JSON 与 `docs/` Markdown 是否保持一致

所有命令把结构化数据写入 `.abh/` 目录（JSON），同时同步生成 `docs/` 下的 Markdown 文档，便于回放、审查和复用。

## 项目价值

这个项目的价值不在于"再做一个任务管理工具"，而在于把 AI 协作中的关键判断拆开：

- 计划和执行分离，避免边做边给自己验收
- 验证和审计分离，减少假完成
- 历史经验显式存档，避免重复踩坑
- 以仓库为中心沉淀长期结构，为跨 session 持续开发提供可追溯的事实记录

对于需要持续迭代、又希望保持结构稳定的工程团队，这种方式比临时性的聊天上下文更可靠。

## 安装

如果你没有 Python 环境，优先看上面的“零基础使用：不装 Python”。本节保留详细安装方式，供需要手动选择运行路径的用户使用。

### 首选方式：uvx（无需安装 Python）

`uv` 是一款代替 pip 的极速包管理工具，会自动下载匹配的 Python 版本。用户只需安装 `uv`，无需手动安装 Python。

安装 uv（如已安装可跳过）：

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

直接运行 abh（uv 自动下载 Python 3.13+ 并构建项目）：

```bash
uvx --from git+https://github.com/worm-ai/harness-before.git abh --help
```

持久安装到 PATH（安装后可在任意目录直接使用 `abh`）：

```bash
uv tool install --from git+https://github.com/worm-ai/harness-before.git abh
abh --help
```

### 备选：手动安装 Python（Python 3.13+）

如果已有 Python 3.13+ 环境，可以走传统 pip 方式。

确认版本：

```bash
python3 --version
```

推荐在仓库根目录做 editable install（Windows 用户请将 `python3` 替换为 `python` 或 `py -3`）：

```bash
python3 -m pip install -e .
```

安装后运行：

```bash
abh --help
```

5 分钟上手路径见 `docs/quickstart.md`。Agent 使用配方见 `docs/recipes/`，其中覆盖 Codex、Claude Code、MCP、hooks、第一个闭环和当前支持的分发方式。

如果没有安装包，也可以在仓库根目录直接运行：

```bash
python3 -m abh --help
```

如果在临时目录或外部目录用源码运行，需要显式提供仓库路径：

```bash
PYTHONPATH=/path/to/harness-before python3 -m abh --help
```

最小验证命令：

```bash
python3 -m unittest tests/test_cli.py
```

## 版本策略

项目版本以 `pyproject.toml` 的 `[project].version` 和 `abh.__version__` 为准，两者必须保持一致。README 中声明的新 CLI 能力、安装方式或运行要求发生变化时，必须同步检查版本是否需要提升，并在对应 plan 的 closure evidence 中说明。

当前发布版本为 `0.7.0`，对应阶段 7 团队可用与生态集成：项目已经具备完整的 Agent-First CLI/MCP 工具链、独立审计门禁、语义压力报告和 CI 模板。阶段 3 Verify Runner、阶段 4 Agent-First 吸引子入口层、阶段 5 独立审计支持、阶段 6 漂移与记忆质量提升均已关闭。阶段 7 的 CI templates、abh-workflow-skill、codex-repo-toggle 已完成；multi-repo-sharing 因缺少 R-flow 实现证据 blocked/deferred；team-policy-and-release-automation 仍待 materialize。受控写工具必须显式传入 `confirm=true`，并复用现有 core 规则，不能绕过 plan 状态机、验证记录、审计关闭门禁或 doctor 一致性检查。

## CI 与关闭门禁

仓库 CI 执行以下基础检查：

```bash
python3 -m unittest discover -v
python3 -m abh doctor --json
python3 -m abh roadmap check --json
git diff --check
python3 -m abh report health --json
```

Gating checks: `unittest`、`doctor`、`roadmap check` 和 `git diff --check` 是当前 CI 模板的 gating 检查；失败表示代码、ABH 对象、roadmap 或 whitespace drift 不满足本地验证契约。

Informational checks: `python3 -m abh report health --json` is informational. 它是只读姿态证据，用于在 PR 中暴露 drift、memory 和 semantic pressure；the workflow does not fail solely because historical semantic pressure exists，也不把历史 health pressure 自动升级为 release blocker 或团队策略。复用模板见 `docs/recipes/ci.md`。

关闭 plan 前也应运行这些命令，并检查 roadmap、task-board、README 等当前状态文档是否需要同步更新。该要求来自 `mem-post-close-doc-sync-001`，用于避免计划关闭后文档仍停留在旧阶段。

## 使用教程

### 1. 创建计划

先创建一个计划，绑定吸引子和基线：

```bash
abh plan create \
  --id plan-001 \
  --title "Sprint 1 Foundation" \
  --attractor docs/architecture/attractors/abh-core-attractor.md \
  --baseline docs/development-roadmap.md \
  --goal "建立标准目录结构" \
  --non-goal "实现路由分析" \
  --exit-criterion "目录与模板文件齐备" \
  --validation "检查 docs 目录结构" \
  --closure-evidence "计划文档与审计记录存在"
```

创建时默认为 `draft` 状态，也可以加上 `--status ready` 直接创建已就绪的计划。可选的 `--owner` 参数用于指定计划负责人。

### 2. 查看计划状态

```bash
abh plan status plan-001
```

### 2.1 查看计划列表

列出所有计划及其当前状态：

```bash
abh plan list
```

### 3. 推进计划状态

计划状态机：`draft → ready → running → closing → closed`（`blocked` 为侧岔路）

```bash
abh plan transition plan-001 --to ready
abh plan transition plan-001 --to running
```

状态迁移有约束：进入 `ready` 前必须有 goals、non-goals、exit criteria 等完整信息；进入 `closing` 前必须有一条通过的验证记录。

### 3.1 更新计划内容

从阶段 3 开始，可以用 `plan update` 追加计划条目，并保持 `.abh/` JSON 与 `docs/` Markdown 双写一致：

```bash
abh plan update plan-017-plan-update \
  --goal "补充新的目标" \
  --validation "python3 -m abh doctor" \
  --closure-evidence "docs/plans/plan-017-plan-update.md"

abh plan update plan-017-plan-update --validation "python3 -m unittest tests/test_cli.py -v" --json
```

`plan update` 当前追加 goals、non-goals、exit criteria、validation checklist 和 closure evidence，并会跳过重复条目。它还支持用 `--remove-validation` 精确移除错误的 validation checklist 条目，用于修复不安全或过期的验证命令。它不提供通用删除、替换、重排，也不改变计划状态。

### 4. 记录验证

```bash
abh verify record plan-001 \
  --command "python -m unittest tests/test_cli.py" \
  --result pass \
  --artifact "tests/test_cli.py"
```

验证结果支持 `pass` / `fail` / `partial`。如果结果为 `fail` 或 `partial` 且计划处于 `ready` 或 `running`，计划会自动转入 `blocked` 状态。验证失败的具体项可以通过 `--failed-check` 记录。

### 4.1 执行验证

从阶段 3 开始，`verify` 支持本地执行计划的 validation checklist：

```bash
abh verify run plan-016-verify-runner
abh verify run plan-016-verify-runner --json
```

`verify run` 会按顺序执行计划中的 validation checklist 命令，并把 stdout/stderr 摘要、退出码和耗时写入 verification artifacts。全部命令成功时记录 `pass`；任一命令失败或超时时记录 `fail`，并沿用现有规则阻断 `ready` 或 `running` 计划。

从 `plan-019-verification-environment-metadata` 开始，`verify run` 还会在 verification JSON 中写入结构化 `environment` 元数据，包括 cwd、git commit、dirty status、git status hash、ABH 版本、Python 版本、timeout、命令 argv 和 allowlisted 环境变量。旧 verification 记录缺少该字段时仍可读取，默认视为空环境快照。`argv` 是从命令字符串派生出的描述性元数据；当前命令仍通过 shell 执行，不应把它理解为真实的 OS exec argv。

从 `plan-021-verification-trust-and-stale-detection` 开始，verification JSON 会保存 `trust_level`。人工 `verify record` 默认为 `manual_record`，本地 `verify run` 默认为 `local_shell`，旧记录缺少该字段时读取为 `unknown`。`abh plan status <plan> --json` 会额外返回 `verification_summary`，展示 latest verification 的 `trust_level`、`stale` 和 `reasons`。当前 stale 是风险提示，不会自动阻断 close。

从 `plan-047-verification-runner-trust-policy` 开始，`verify run` 的 environment runner metadata 会显式记录 `execution_policy=guarded_local_shell`、`trust_level=local_shell`、`command_source=plan_validation_checklist` 和 `isolation=none`。含义是 ABH 在当前 workspace 通过本地 shell 执行计划中已审阅的 validation checklist；它不是隔离环境、不是 CI attestation、不是防篡改证明，也不表示未审阅的外部命令可以安全自动执行。

从 `plan-022-verification-failure-classification` 开始，失败的 `verify run` 会保存 `failure_classifications`，把非零退出、超时、递归防护和本地 runner 执行异常分别标记为 `validation_failure`、`timeout`、`recursive_guard` 和 `environment_failure`。该字段只增强审计证据表达，不改变 `pass` / `fail` / `partial` 语义，也不改变 ready/running 失败阻断规则。

这些 checklist 条目按本地 shell 命令解释执行，适合仓库内受信任的验证命令。当前 runner policy 是 `guarded_local_shell`：命令来源限定为 plan validation checklist，执行隔离级别为 `none`。当前 MVP 不提供隔离环境、CI runner、远程 runner 或额外确认提示。

### 5. 发起审计

```bash
abh audit request plan-001 \
  --id audit-001 \
  --auditor "independent-review" \
  --scope "检查计划是否满足关闭条件" \
  --evidence "docs/plans/plan-001.md"
```

审计请求至少需要一条 evidence 引用（通常为文件路径）。审计记录会同时保存为 `.abh/audits/` 下的 JSON 和 `docs/audits/` 下的 Markdown。

阶段 5 开始，`abh audit bundle <plan> --json` 可以从现有 plan 状态生成只读审计提示词和证据清单：

```bash
abh audit bundle plan-001 --json
```

该 bundle 会包含计划元数据、最新 verification freshness 摘要、已请求 audit、closure evidence 和可复制给独立审计者的 prompt。它不会调用模型、不会写入 audit record、不会 transition/close plan，也不会替代独立审计判断。

### 6. 记录审计结论

```bash
abh audit record audit-001 \
  --result pass \
  --rationale "证据完整，计划满足关闭条件" \
  --auditor-context "opencode isolated session using DeepSeek V4 Pro" \
  --independence independent \
  --verification-id ver-123456789abc \
  --finding "Low|No blocking issue|tests/test_cli.py|No action"
```

`--finding` 格式为 `Severity|Finding|Evidence|Recommendation`，支持多次传入。阶段 5 的关闭门禁要求通过审计同时声明 `--independence independent`，并用 `--verification-id` 绑定当前最新且 fresh 的 passing verification；`--auditor-context` 用于记录审计来源或隔离上下文。审计结论可以重复记录（后一次覆盖前一次）。

### 7. 查看审计列表

列出所有审计及其结果：

```bash
abh audit list
```

### 8. 关闭计划

关闭条件：计划必须有至少一条通过（`pass`）的审计记录，并且 `closure_evidence` 非空。

```bash
abh close plan-001
```

### 9. 记录和检索记忆

记忆用于记录被证伪的假设、被拒绝的路径、发散模式和被推翻的完成判断。

```bash
abh memory add \
  --id mem-001 \
  --type false_assumption \
  --summary "某条路径无法稳定收敛" \
  --context "在重复验证中出现漂移" \
  --implication "后续不要再作为默认方案" \
  --evidence "docs/audits/audit-001.md" \
  --tag quality-signal \
  --status active \
  --related-plan plan-001

abh memory search --query "漂移"
abh memory search --status active --tag quality-signal --related-plan plan-001 --json
```

记忆搜索使用子字符串匹配（不区分大小写）。如需更精确的范围，可以用 `--type`、`--status`、`--tag`、`--related-plan`、`--related-audit` 和 `--related-drift` 过滤。从 Stage 6 Memory Index 开始，memory JSON 和 Markdown 会保留 `tags`、`status`、`related_plan_ids`、`related_audit_ids`、`related_drift_ids` 与 `superseded_by`，让过去经验能按关系和有效性复用。

### 10. 列出记忆记录

列出所有记忆记录：

```bash
abh memory list
```

### 11. 路由和漂移分析

根据问题输出建议阅读顺序：

```bash
abh route --question "Can we close this plan?"
```

`route` 现在会自动注入当前正在运行或阻塞中的计划，以及关键词相关的记忆记录，帮助更快定位上下文。

对文本证据做基础漂移分析。先准备一份漂移源文件：

```bash
echo "Imported a remote database dependency even though the plan said no external database." > drift-source.txt
```

然后执行分析，并把漂移模式写入 memory：

```bash
abh drift analyze \
  --id drift-001 \
  --source drift-source.txt \
  --evidence drift-source.txt \
  --memory-id mem-drift-001

abh memory search --type divergent_pattern --query dependency
```

漂移分析基于本地关键词规则识别四类漂移：边界漂移、依赖漂移、测试漂移和术语漂移。从 Stage 6 开始，JSON 和 MCP 输出中的 drift finding 会携带质量信号字段：`severity`、`confidence`、`rule_id`、`matched_span`、`source_excerpt` 和 `evidence_path`。这些字段用于先判断产品质量风险，再供后续 memory、route、`abh next` 和 health report 消费。

从 v0.2.0 开始，`drift analyze` 支持 `--plan` 参数，以计划的 non-goals 为基线检测范围违规：

```bash
abh drift analyze --id drift-002 --source drift-source.txt --plan plan-007
```

### 11b. 结构化范围检查（plan-bound structural drift）

从 plan-058 开始，`close_plan` 会在关闭前自动检查代码变更是否超出 plan 声明的范围：

```bash
# 创建一个带 scope 的计划
abh plan create \
  --id plan-struct-demo \
  --title "Add auth module" \
  --attractor docs/architecture/attractors/abh-core-attractor.md \
  --baseline "baseline" \
  --goal "add auth module under src/auth/" \
  --non-goal "不引入新数据库依赖" \
  --scope src/auth \
  --validation "python3 -m pytest" \
  --closure-evidence tests/

# 开发完成后，close 时会自动检查：
# 1. git diff <baseline_commit> → 列出所有变更文件
# 2. 变更文件是否都在 scope 内（src/auth/）
# 3. 新增 import 是否匹配 non-goal 关键词
# 4. 违规 → 拒绝关闭，给出具体文件和建议

abh close plan-struct-demo
# 如果 src/payment/ 被改了 → AbhError:
#   "plan scope check failed; cannot close: src/payment/handler.py outside scope ['src/auth']"
```

也可以单独运行检查：

```bash
abh drift plan-check plan-struct-demo --json
```

Plan 的 `baseline_commit` 在 `plan create` 时自动从当前 HEAD 捕获，作为 diff 比较的基线。如果 plan 创建时没有 git，scope check 会静默跳过。如果 scope 为空且 goals 中没有路径关键词，会返回 `need_info` finding 要求用户声明 `--scope`。

`PlanRecord` 新增 `scope: list[str]` 字段（可选），显式声明计划允许修改的目录范围。`--scope` 参数同时支持 CLI 和 MCP。

### 12. 检查工作区一致性

`doctor` 用于检查核心对象的 JSON 记录和 Markdown 文档是否一一对应：

```bash
abh doctor
```

输出 `doctor: ok` 表示 `.abh/plans`、`.abh/audits`、`.abh/memory`、`.abh/drift` 与对应 `docs/` 目录一致。若发现缺失文档或孤儿文档，命令会列出问题并返回非零状态码，适合放入 CI 或 plan 关闭前检查。

### 13. JSON 输出模式

面向 Agent Protocol 的只读命令支持显式 `--json` 输出。默认输出仍保持人类可读文本；只有传入 `--json` 时才输出机器可解析 envelope。

```bash
abh plan list --json
abh plan status plan-013-json-output-and-errors --json
abh audit list --json
abh memory list --json
abh memory search --query audit --json
abh route --question "Can we close this plan?" --json
abh audit bundle plan-037-audit-prompt-bundle --json
abh report health --json
abh doctor --json
```

JSON envelope 包含 `schema_version`、`ok`、`command`、`data`、`errors` 和 `warnings`。当 ABH 业务错误发生时，`--json` 模式会把错误写入 `errors`，并保留现有返回码语义。

### 14. Agent Setup Export

阶段 4 开始，ABH 可以导出面向具体 Agent 或通用 MCP 客户端的只读 setup bundle。该命令读取 active attractor、AGE owner docs 和共享命令契约，只输出推荐阅读、工作流规则、推荐命令和写入边界；当前切片不会写入 `AGENTS.md`、`CLAUDE.md`、MCP 配置或 hooks。

```bash
abh agent setup codex --json
abh agent setup claude-code --json
abh agent setup mcp --json
```

`mcp` 目标会包含当前 MCP server 启动命令：

```bash
python3 -m abh.mcp_server
```

### 14.1 Codex Repository Toggle

如果你希望当前仓库在 Codex 桌面版中默认以 ABH 流程工作，可以写入仓库级受管配置：

```bash
abh codex status --json
abh codex on --write --confirm --json
abh codex off --write --confirm --json
```

`abh codex on --write --confirm --json` 会创建受管 `.codex/config.toml`，把 `skills/abh-workflow`、`abh onboarding check --json`、`abh next --json`、`abh doctor --json` 和 `abh roadmap check --json` 注入 Codex 的 `developer_instructions`。该命令默认是 preview-only；只有同时传入 `--write --confirm` 才会写文件。若当前仓库已有 unmanaged `.codex/config.toml`，命令会返回 blocker，不会覆盖用户配置。

### 15. Git Hook Guardrails

阶段 4 的 hook guardrails 提供本地 pre-commit 保护层。默认 profile 是一个轻量 `pre-commit` hook，会运行：

```bash
python3 -m abh doctor
python3 -m abh roadmap check --json
git diff --check
```

预览不会写入仓库：

```bash
abh hooks profile --json
abh hooks install --json
```

安装必须显式确认：

```bash
abh hooks install --write --confirm --json
```

该命令只会创建或刷新带有 `ABH MANAGED PRE-COMMIT` 标记的 `.git/hooks/pre-commit`。如果已有非 ABH 管理的 hook，它会返回 blocker，不会覆盖用户现有脚本。团队策略、远程分发、strict profile 和发布自动化仍是后续阶段范围。

### 16. Agent Navigation and Onboarding

`abh next --json` 是 Agent 的默认导航入口。它读取本地 plan、roadmap queue 和状态机信息，返回下一条建议动作、推荐命令、是否需要确认、依据和备选命令。当前 MVP 优先处理已有 open plan；有 fresh passing verification 但尚无 audit 时推荐请求独立审计，没有 open plan 时推荐 materialize 下一条 queued roadmap item。

```bash
abh next --json
```

`abh onboarding check --json` 是只读 readiness 报告。它检查 active attractor、AGE owner docs、agent setup export、hook guardrail commands、doctor 和至少一个 verify/audit/close 闭环证据，并返回每项 check 的 status、details 和 recommended action。

```bash
abh onboarding check --json
```

这两个命令不写入仓库，不安装 hook，不写 Agent 配置，也不替代 route/drift 或 audit 判断。

### 17. Project Health Report

`abh report health --json` 是只读质量报告。它读取本地 plan、verification、audit、drift、memory、doctor 和 roadmap queue，输出 health metrics、semantic pressure signals、top risks 和 recommended inspections。

```bash
abh report health --json
```

当前报告会暴露 `stale_proof`、`repeated_leakage`、`orphaned_memory` 和 `j_flow_only_evidence` 等语义压力信号。它用于帮助人和 Agent 决定下一步检查什么，不会自动阻塞 plan close、release 或 audit verdict。

### 18. MCP Server

ABH 提供一个零外部运行时依赖的 MCP stdio Server，供支持 MCP 的 Agent 通过工具协议读取治理状态，并在显式确认后执行受控写操作：

```bash
python3 -m abh.mcp_server
```

当前只读 MCP 工具：

- `abh_plan_list`
- `abh_plan_status`
- `abh_audit_list`
- `abh_memory_list`
- `abh_memory_search`
- `abh_route`
- `abh_doctor`
- `abh_drift_list`
- `abh_report_health`

当前受控写 MCP 工具：

- `abh_plan_create`
- `abh_plan_transition`
- `abh_verify_record`
- `abh_audit_request`
- `abh_audit_record`
- `abh_close_plan`
- `abh_memory_add`
- `abh_drift_analyze`

所有 MCP 工具都复用现有 `.abh/` JSON 和 core/model 行为，返回包含 `structuredContent` 的 MCP tool result。写工具必须传入 `confirm=true`，否则返回结构化业务错误并且不写入仓库。

## 项目结构

- `abh/`：CLI 和核心逻辑
- `docs/index.md`：Agent 和维护者进入仓库时的文档路由入口
- `docs/context/`：项目上下文、真相源优先级、约定和代码地图
- `docs/architecture/`：吸引子与架构说明
- `docs/plans/`：计划文档（Markdown）
- `docs/audits/`：审计文档（Markdown）
- `docs/memory/`：记忆文档（Markdown）
- `docs/drift/`：漂移分析报告（Markdown）
- `.abh/`：运行时结构化数据（JSON），与 `docs/` 下的文档双向同步
- `tests/`：测试用例（unittest）

## 适用场景

- AI 参与的持续开发
- 需要审计闭环的工程流程
- 希望沉淀决策、反例和失败经验的仓库
- 需要把"完成"定义得更严格的项目

## 后续演进

当前仓库已覆盖计划、验证、审计、关闭、记忆、路由、漂移分析、MCP Server、Agent setup、Git hooks、health report 和 CI templates。67 个 plan 全部关闭。

### 已完成阶段

- **阶段 1（v0.1）**：恢复权威基线 — 目录结构、模板、doctor、CI、schema version、版本策略
- **阶段 2（v0.2）**：Agent Protocol 基础 — JSON CLI contract、结构化错误、只读 MCP、受控 MCP 写工具
- **阶段 3（v0.3）**：Verify Runner — 本地验证执行、环境元数据、可信等级、stale 检测、失败分类、原子写、领域模块拆分
- **阶段 4（v0.4）**：Agent-First 吸引子入口层 — attractor registry、roadmap queue、AGE owner docs、`abh init`、agent setup、git hooks、`abh next`/onboarding check、quickstart/recipes
- **阶段 5（v0.5）**：独立审计支持 — audit prompt bundle、independent audit gate（auditor context、independence 声明、fresh verification basis）
- **阶段 6（v0.6）**：漂移与记忆质量提升 — quality signal model、drift quality、memory index、health report、command contract runtime registry、write transaction boundary、schema validation/migration、verification runner trust policy、test suite domain split、commitment phase state、audit semantic conservation、owner doc stable commitments、post-close freshness semantics

### 阶段 7（v0.7，进行中）

已完成：
- `plan-053-ci-templates`：GitHub Actions ABH CI 模板
- `plan-055-abh-workflow-skill`：Codex 傻瓜式 skill 封装
- `plan-056-readme-zero-python-skill-onboarding`：零基础用户 README 和小白 skill 入口
- `plan-057-codex-repo-toggle`：Codex 仓库级 ABH toggle
- `plan-058-verification-sandbox-and-storage-hardening`：验证沙箱与存储硬化
- `plan-060-signal-quality-hardening`：信号质量硬化（stale severity 重分类 + memory triage）
- `plan-061-drift-detection-depth`：漂移检测深度提升（terminology drift）
- `plan-062-agent-ux-phase-a`：Phase A — 零摩擦 Agent UX（smart defaults + plan run/finish）
- `plan-063-agent-ux-phase-b`：Phase B — 全局感知仪表板 + memory 注入 `abh next`
- `plan-064-agent-ux-phase-c`：Phase C — Agent-to-Agent 审计协议
- `plan-065-memory-active-injection`：`plan status` 自动注入相关 memory
- `plan-066-audit-protocol-v2`：自包含审计包
- `plan-067-plan-complete`：`abh plan complete` 端到端意图执行

已关闭（实现范围受限或审计未通过）：
- `plan-043-plan-reference-set`：已关闭，实现内容 deferred
- `plan-054-multi-repo-sharing`：已关闭，独立审计确认缺少 R-flow 实现证据，待重新 materialize

Roadmap queue 剩余待 materialize（4 项）：
- `stage7.multi-repo-sharing`
- `stage7.team-policy-and-release-automation`
- `stage7.attractor-export-import`
- `stage7.memory-sharing-format`

### 未来方向

- 补齐 multi-repo sharing 的 R-flow 实现证据后重新 materialize
- 团队策略配置与发布自动化
- Attractor 导出/导入 bundle
- Memory 共享格式标准化
- 从关键词漂移检测升级到更高质量的证据提取
- 扩展 Git hook 集成到团队策略和更多 profile
- 为验证记录增加更细粒度执行证据，与 closure evidence 形成完整可追溯链路
