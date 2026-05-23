# Architecture

本目录承载项目的吸引子定义、架构原则和结构基线。

## Reading Order

1. `attractors/`：当前系统应长期收敛到的稳定结构。
2. `agent-protocol.md`：AI Agent 可程序化读写 ABH 的协议基线。
3. `policies/`：跨模块规则和治理策略。
4. `templates/`：架构文档模板。

## Authority

- 问“系统应该向哪里收敛”，以 active attractor 为准。
- 问“当前实现是什么”，以代码和测试为准。
- 问“某轮任务如何收口”，以对应 plan 为准。

## Active Attractor

- `attractors/abh-core-attractor.md`
