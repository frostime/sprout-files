# project-command-discovery Specification

## Purpose
TBD - created by archiving change sprout-template-driven-cli. Update Purpose after archive.
## Requirements
### Requirement: Project template root discovery SHALL use nearest ancestor
The CLI MUST discover the project template root by starting from the current working directory and walking upward. It SHALL stop at the first directory containing `.<cli-name>/` (current default: `.sprout/`).

#### Scenario: Discover root from nested subdirectory
- **WHEN** the user runs `sprout` inside a nested folder of a configured project
- **THEN** the CLI finds the nearest ancestor containing `.sprout/` and uses it as the only active template root

#### Scenario: No root found
- **WHEN** the user runs `sprout` in a directory tree with no `.sprout/`
- **THEN** the CLI exits with a clear error explaining that no project template root was found

### Requirement: Command packages SHALL be loaded from a fixed command directory
The CLI MUST load command definitions only from `.<cli-name>/commands/<command>/` under the discovered root.

#### Scenario: Valid command package is discoverable
- **WHEN** a directory `.sprout/commands/change/` contains a valid manifest
- **THEN** command `change` appears in available commands

### Requirement: Duplicate command names MUST be disabled deterministically
If two command packages resolve to the same command name within one discovered root, the CLI MUST disable both conflicting commands and MUST emit a warning with both source paths.

#### Scenario: Duplicate command name conflict
- **WHEN** two command packages both declare command name `change`
- **THEN** neither package is executable and the CLI outputs a conflict warning with remediation guidance

### Requirement: Invalid command definitions MUST be isolated
If a command package is invalid (schema error, missing required fields, unreadable manifest), the CLI MUST mark only that command as unavailable and MUST continue loading other valid commands.

#### Scenario: One invalid package among valid packages
- **WHEN** package `issue` is valid and package `change` has malformed manifest
- **THEN** `issue` remains executable and `change` is reported as invalid with error details

