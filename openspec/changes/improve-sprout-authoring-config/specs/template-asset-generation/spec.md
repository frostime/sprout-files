## MODIFIED Requirements

### Requirement: `new` command MUST generate assets from command definition
The CLI SHALL execute `sprout new <command>` by loading the command package, validating inputs, resolving variables, and creating all declared assets, regardless of whether the command definition is authored in YAML, JSON, or TOML.

#### Scenario: Generate directory and file assets
- **WHEN** command `change` declares a directory asset and a file asset using the same variable set
- **THEN** the CLI creates the directory first and then creates the file at the rendered path

### Requirement: Existing target path handling MUST be policy-driven
The CLI MUST support project-configured conflict policy for existing target paths: `fail`, `overwrite`, `skip`, and `rename`.

#### Scenario: Fail policy
- **WHEN** policy is `fail` and a rendered target already exists
- **THEN** the CLI aborts generation and reports the conflicting path

#### Scenario: Overwrite policy
- **WHEN** policy is `overwrite` and a rendered target already exists
- **THEN** the CLI replaces the existing target with generated content

#### Scenario: Skip policy
- **WHEN** policy is `skip` and a rendered target already exists
- **THEN** the CLI leaves the existing target unchanged and continues with other assets

#### Scenario: Rename policy
- **WHEN** policy is `rename` and a rendered target already exists
- **THEN** the CLI writes output to a non-conflicting path using deterministic suffixing and reports the remapped path

## ADDED Requirements

### Requirement: Project config loading MUST support YAML-first authoring
The CLI MUST load project configuration from `.sprout/config.yaml` or `.sprout/config.yml` when present, and MUST continue supporting equivalent TOML or JSON project config files for backward compatibility.

#### Scenario: YAML project config is present
- **WHEN** `.sprout/config.yaml` exists with a valid `conflict` policy
- **THEN** the CLI uses that YAML configuration as the project-level generation policy

#### Scenario: Legacy JSON project config remains in use
- **WHEN** `.sprout/config.json` exists and no YAML project config is present
- **THEN** the CLI continues to load the JSON configuration without requiring migration
