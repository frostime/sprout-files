# agent-assisted-template-authoring Specification

## Purpose
TBD - created by archiving change sprout-template-driven-cli. Update Purpose after archive.
## Requirements
### Requirement: `init` command MUST bootstrap project template workspace
The CLI SHALL provide `sprout init` to create the project template workspace under `.<cli-name>/` (current default: `.sprout/`), including command root structure needed for authoring.

#### Scenario: Initialize in a clean project
- **WHEN** the user runs `sprout init` in a project with no `.sprout/`
- **THEN** the CLI creates `.sprout/` and `.sprout/commands/` with baseline authoring assets

### Requirement: `init` MUST support customizable scaffold output
The initialization flow MUST allow selecting or declaring a custom scaffold profile, and MAY include optional example command packages.

#### Scenario: Initialize with custom scaffold
- **WHEN** the user chooses a custom scaffold profile during `sprout init`
- **THEN** the CLI generates the requested skeleton structure and template placeholders defined by that profile

#### Scenario: Initialize with examples enabled
- **WHEN** the user enables examples during `sprout init`
- **THEN** the CLI creates sample command packages (e.g., `issue`/`change`) alongside the base skeleton

### Requirement: `init` MUST be safe on re-run
Running `sprout init` multiple times MUST NOT destroy existing user-authored command packages.

#### Scenario: Re-run init after custom commands exist
- **WHEN** `.sprout/commands/change/` already exists and user runs `sprout init` again
- **THEN** the CLI preserves existing command packages and reports what was skipped or already present

### Requirement: Built-in authoring skill documentation MUST be project-local
The system MUST provide `sprout-authoring` skill documentation within the project workspace and MUST NOT require global skill installation to use project authoring guidance.

#### Scenario: Skill docs generated locally
- **WHEN** `sprout init` completes
- **THEN** the project contains local `sprout-authoring` skill documentation that Agents can read for command package authoring guidance

### Requirement: Authoring flow MUST encourage requirement alignment before file edits
The `sprout-authoring` guidance MUST instruct Agents to align on command purpose, inputs, and output assets before generating or modifying package files.

#### Scenario: User request is underspecified
- **WHEN** a user asks to add a new command without defining required inputs or output paths
- **THEN** the guidance prompts for missing decisions before finalizing package structure

