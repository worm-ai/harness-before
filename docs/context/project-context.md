# Project Context

## Purpose

Attractor Before Harness is a Git-native, evidence-first governance layer for AI-assisted software development. Its job is to keep long-running Agent work converging around explicit attractors instead of temporary chat context.

ABH is not a general project management platform. It is a local-first control plane for plans, verification, audit, memory, drift detection, roadmap queueing, and Agent-facing command contracts.

## Current Product Shape

- CLI package: `abh`
- Storage: `.abh/` JSON records as machine-readable state
- Human-readable mirror: `docs/` Markdown records
- Agent interfaces: explicit JSON CLI envelopes and MCP stdio tools
- Current release line: v0.3 Verify Runner complete; Stage 4 Agent-First attractor entry in progress

## Current Active Attractor

The active attractor is `docs/architecture/attractors/abh-core-attractor.md`. Every executable plan must bind to the current active attractor by id or path before it can become ready.

## Current Stage

Stage 4 makes ABH agent-first:

- active attractor is CLI/MCP readable
- command metadata is shared through `abh.commands`
- future repository initialization must bind new workspaces to the active attractor
- future Agent navigation should answer what to do next, not only what to read

## Non-Goals

- Do not replace Git as the source of truth.
- Do not replace independent audit with local verification.
- Do not weaken the plan close audit gate for convenience.
- Do not build a Web UI before the CLI, JSON, MCP, and init/onboarding path are stable.
