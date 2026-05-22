# Attractor Before Harness

`Attractor Before Harness` 是一个面向 AI 协作开发的收敛框架与 CLI 工具集。项目核心思想来自“先定义系统要收敛到哪里，再用 harness 持续纠偏”的方法论：先把吸引子、基线、计划、验证、审计和记忆显式化，再让开发过程围绕这些对象运行。

## 项目来源

这个项目源于对 AI 大规模开发协作方式的整理与工程化尝试，重点解决三个问题：

1. AI 生成结果不稳定，容易偏离长期目标。
2. 单次任务完成不等于系统轨迹正确。
3. 缺少可审计、可回放、可沉淀的开发过程记录。

因此，本项目把“吸引子”作为长期结构基线，把“harness”作为围绕基线运行的控制层，目标是让仓库本身成为事实来源，而不是把判断留在人的临时记忆里。

## 项目功能

当前项目提供一个名为 `abh` 的命令行工具，支持以下能力：

- `plan`：创建、查看和迁移计划状态
- `verify`：记录验证命令及其结果
- `audit`：发起和记录独立审计
- `close`：在满足条件后关闭计划
- `memory`：记录和检索外部化记忆

这些命令会把结构化数据写入仓库，配套生成文档，便于后续回放、审查和复用。

## 项目价值

这个项目的价值不在于“再做一个任务管理工具”，而在于把 AI 协作中的关键判断拆开：

- 计划和执行分离，避免边做边给自己验收
- 验证和审计分离，减少假完成
- 历史经验显式存档，避免重复踩坑
- 以仓库为中心沉淀长期结构，便于多人、多轮 session 协作

对于需要持续迭代、又希望保持结构稳定的工程团队，这种方式比临时性的聊天上下文更可靠。

## 安装

项目使用 Python 3.13+。

```bash
pip install -e .
```

安装后可以直接使用：

```bash
abh --help
```

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

### 2. 查看计划状态

```bash
abh plan status plan-001
```

### 3. 推进计划状态

```bash
abh plan transition plan-001 --to ready
abh plan transition plan-001 --to running
```

### 4. 记录验证

```bash
abh verify record plan-001 \
  --command "pytest" \
  --result pass \
  --artifact "tests/test_cli.py"
```

### 5. 发起审计

```bash
abh audit request plan-001 \
  --id audit-001 \
  --auditor "independent-review" \
  --scope "检查计划是否满足关闭条件" \
  --evidence "验证结果已通过"
```

### 6. 记录审计结论

```bash
abh audit record audit-001 \
  --result pass \
  --rationale "证据完整，计划满足关闭条件" \
  --finding "无阻塞问题"
```

### 7. 关闭计划

```bash
abh close plan-001
```

### 8. 记录和检索记忆

```bash
abh memory add \
  --id mem-001 \
  --type false_assumption \
  --summary "某条路径无法稳定收敛" \
  --context "在重复验证中出现漂移" \
  --implication "后续不要再作为默认方案" \
  --evidence "audit-001"

abh memory search --query "漂移"
```

## 项目结构

- `abh/`：CLI 和核心逻辑
- `docs/architecture/`：吸引子与架构说明
- `docs/plans/`：计划文档
- `docs/audits/`：审计文档
- `docs/memory/`：记忆体系
- `tests/`：测试用例

## 适用场景

- AI 参与的持续开发
- 需要审计闭环的工程流程
- 希望沉淀决策、反例和失败经验的仓库
- 需要把“完成”定义得更严格的项目

## 后续演进

当前仓库已经覆盖计划、验证、审计、关闭和记忆，后续可继续扩展路由、漂移分析和自动化决策能力，让 harness 更完整地支持长期收敛。
