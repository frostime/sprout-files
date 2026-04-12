# .sprout workspace

Project-local template command workspace for `sprout`.

Start with `.sprout/config.yaml` and `.sprout/commands/<name>/manifest.yaml`.

## Quick checks

```bash
sprout list --all
sprout doctor
sprout new <command> name=test
sprout new <command> --json '{"name":"test"}'
```

Notes:
- TTY terminals can offer interactive fill-in for missing required inputs
- Non-TTY environments fail fast instead of waiting for input
- Use `--json` / `--json-file` for Agent or script-driven calls
