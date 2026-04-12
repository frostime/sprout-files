# Project Context

<!-- This file is the stable identity layer for agents working on this project.
Read it first every session. Update Conventions + Notes via @memory. -->

**Name**: sprout-cli  
**Description**: Template-driven file and directory generator for project workflows, designed for Agent-assisted development  
**Repo**: H:/SrcCode/playground/sprout-cli

## Tech Stack
- Python 3.10+
- CLI framework: argparse
- Build system: hatchling
- Package manager: uv
- Config formats: YAML (primary), JSON (runtime compatible)

## Key Paths
<!-- @RULE: Most important directories/files for quick navigation.
Keep ≤10 entries. Agent uses this to orient in the codebase. -->

| Path | Purpose |
|------|---------||
| `sprout/` | Core package source |
| `sprout/cli.py` | CLI entry point and command handlers |
| `sprout/core.py` | Discovery, loading, rendering, generation logic |
| `sprout/models.py` | Data models and type definitions |
| `sprout/scaffold.py` | `init` command implementation and profiles |
| `tests/` | Test suite |
| `README.md` | User-facing documentation |
| `.sprout/` | Example workspace (created by `sprout init`) |

## Conventions
<!-- @RULE: Coding rules that apply across ALL work in this project.
One-liners only. If a convention needs multi-paragraph explanation → write a spec-doc.
Examples: "snake_case for Python, camelCase for JS", "All API routes: /api/v1/*",
"Never commit .env files", "Prefer composition over inheritance" -->

- Python 3.10+ with `from __future__ import annotations` for forward references
- Use dataclasses with `slots=True` for models
- snake_case for functions, PascalCase for classes
- Type hints required for all public APIs
- Literal types for enums (ConflictPolicy, InputType, AssetType)
- Custom exceptions inherit from `SproutError` base
- Discovery pattern: walk up from cwd to find `.sprout/` (like `.git`)
- Template syntax: `{{variable}}` for simple text interpolation only
- Config priority: command manifest > project config > CLI args
- Entry point: `sprout = "sprout.cli:main"` in pyproject.toml

## Spec-Docs Index
<!-- @RULE: Quick reference to formal specs in `.sspec/spec-docs/`.
Agent reads this to know what architecture knowledge exists before starting work.
Keep entries in sync with actual spec-doc files. Format: `- [name](spec-docs/<file>) — one-line description` -->

- [sprout-architecture](spec-docs/sprout-architecture.md) — Core runtime architecture: discovery, registry, template system, generation pipeline, conflict resolution

## Notes
<!-- @RULE: Project-level memory. Append-only log of learnings, gotchas, preferences.
Agent appends here during @memory when a discovery is project-wide (not change-specific).
Format each entry as: `- YYYY-MM-DD: <learning>`
Prune entries that become outdated or graduate to Conventions/spec-docs. -->

- 2026-04-11: Project initialized with SSPEC protocol. Core implementation complete with init/list/doctor/new commands. Uses upward discovery pattern for `.sprout/` directory. Supports YAML/TOML/JSON manifests at runtime. Template engine is simple text replacement only (no logic/conditionals).
- 2026-04-11: `sprout new` now supports structured input via `--json` and `--json-file`, with TTY-only interactive fallback and `--no-input` for explicit non-interactive runs.
- 2026-04-11: Default scaffold examples use `issue` and `task`; avoid `change` as a user-facing example name to prevent confusion with this repo's `.sspec` workflow.
