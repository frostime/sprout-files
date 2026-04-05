# template-asset-generation Specification

## Purpose
TBD - created by archiving change sprout-template-driven-cli. Update Purpose after archive.
## Requirements
### Requirement: `new` command MUST generate assets from command definition
The CLI SHALL execute `sprout new <command>` by loading the command package, validating inputs, resolving variables, and creating all declared assets.

#### Scenario: Generate directory and file assets
- **WHEN** command `change` declares a directory asset and a file asset using the same variable set
- **THEN** the CLI creates the directory first and then creates the file at the rendered path

### Requirement: Input collection MUST default to non-interactive mode
The CLI MUST treat command-line arguments and flags as the default input source. It SHALL enter prompt-based interaction only when `-i` or `--interactive` is explicitly provided.

#### Scenario: Missing required input without interactive flag
- **WHEN** required input `name` is not provided and `-i/--interactive` is absent
- **THEN** the CLI fails with a validation error listing missing inputs

#### Scenario: Missing required input with interactive flag
- **WHEN** required input `name` is not provided and `-i` is present
- **THEN** the CLI prompts for `name` and continues after valid input is provided

### Requirement: Input type validation SHALL support basic scalar types
The CLI MUST validate declared input types `string`, `number`, and `enum` before rendering assets.

#### Scenario: Enum value validation
- **WHEN** input `type` is declared as enum `[bug, feat, refactor]` and user passes `hotfix`
- **THEN** the CLI rejects the input and reports allowed enum values

### Requirement: Number constraints SHALL support optional min/max
When an input is declared as `number`, the command definition MAY provide `min` and/or `max`. If present, the CLI MUST enforce these boundaries.

#### Scenario: Number below min
- **WHEN** input `priority` is declared as `number` with `min: 1` and user provides `0`
- **THEN** the CLI rejects the value and reports that it is lower than the minimum

### Requirement: Template rendering MUST use plain text variable interpolation
The CLI MUST support `{{variable}}` interpolation in both asset paths and template file contents. v0.1 MUST NOT execute control-flow logic (if/for/functions).

#### Scenario: Interpolate variable in path and content
- **WHEN** asset path is `issues/{{YY}}-{{MM}}-{{DD}}_{{name}}.md` and template content contains `# {{name}}`
- **THEN** the CLI writes a file with all placeholders replaced by resolved variable values

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

