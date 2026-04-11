## MODIFIED Requirements

### Requirement: `init` command MUST bootstrap project template workspace
The CLI SHALL provide `sprout init` to create the project template workspace under `.<cli-name>/` (current default: `.sprout/`), including command root structure needed for authoring, and the default scaffold MUST use YAML configuration files with inline guidance comments.

#### Scenario: Initialize in a clean project
- **WHEN** the user runs `sprout init` in a project with no `.sprout/`
- **THEN** the CLI creates `.sprout/` and `.sprout/commands/` with baseline authoring assets
- **AND** the generated project config and example command manifests use YAML as the default authoring format

### Requirement: `init` MUST support customizable scaffold output
The initialization flow MUST allow selecting or declaring a custom scaffold profile, and MAY include optional example command packages.

#### Scenario: Initialize with custom scaffold
- **WHEN** the user chooses a custom scaffold profile during `sprout init`
- **THEN** the CLI generates the requested skeleton structure and template placeholders defined by that profile

#### Scenario: Initialize with examples enabled
- **WHEN** the user enables examples during `sprout init`
- **THEN** the CLI creates sample command packages (e.g., `issue`/`change`) alongside the base skeleton
- **AND** the sample command manifests are emitted as YAML with inline comments and example values

### Requirement: Built-in authoring skill documentation MUST be project-local
The system MUST provide `sprout-authoring` skill documentation within the project workspace and MUST NOT require global skill installation to use project authoring guidance.

#### Scenario: Skill docs generated locally
- **WHEN** `sprout init` completes
- **THEN** the project contains local `sprout-authoring` skill documentation that Agents can read for command package authoring guidance
- **AND** the guidance explains the supported `.sprout` data model, field meanings, and recommended YAML structure

### Requirement: Authoring flow MUST encourage requirement alignment before file edits
The `sprout-authoring` guidance MUST instruct Agents to align on command purpose, inputs, and output assets before generating or modifying package files.

#### Scenario: User request is underspecified
- **WHEN** a user asks to add a new command without defining required inputs or output paths
- **THEN** the guidance prompts for missing decisions before finalizing package structure

## ADDED Requirements

### Requirement: Authoring guidance MUST explain how to fill `.sprout` files
The project-local authoring guidance MUST provide explicit field-by-field instructions for `.sprout` project config and command manifests, including supported values, defaults, and complete examples.

#### Scenario: Agent needs to create a command package
- **WHEN** an Agent reads `.sprout/skills/sprout-authoring/SKILL.md` before authoring a command package
- **THEN** the guidance tells the Agent which files to create or edit
- **AND** the guidance explains how to fill `inputs`, `assets`, conflict policy, and template references without requiring source-code inspection
