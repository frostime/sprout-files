from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Sequence

from . import __version__
from .core import (
    VALID_CONFLICT_POLICIES,
    apply_generation_plan,
    build_generation_plan,
    build_variable_context,
    collect_inputs,
    effective_conflict_policy,
    execute_actions,
    find_missing_required_inputs,
    load_json_input_file,
    load_registry,
    merge_input_sources,
    parse_json_input,
    parse_key_value_pairs,
    plan_post_actions,
    suggest_command_names,
    validate_template_variables,
)
from .models import DiscoveryError, GenerationError, UserAbortError, ValidationError
from .scaffold import initialize_workspace


def _docs_dir() -> Path:
    return Path(__file__).parent / 'docs'


def _user_guide_path() -> Path:
    return _docs_dir() / 'user-guide.md'


def _builtin_docs() -> dict[str, Path]:
    docs_dir = _docs_dir()
    return {
        'user-guide': docs_dir / 'user-guide.md',
        'command-authoring-guide': docs_dir / 'command-authoring-guide.md',
    }


def _build_parser() -> argparse.ArgumentParser:
    guide = _user_guide_path()
    parser = argparse.ArgumentParser(
        prog="sprout",
        description="Template-driven project generator",
        epilog=f"User guide: {guide}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"sprout {__version__}")

    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Initialize .sprout workspace")
    init_parser.add_argument(
        "--profile",
        default="minimal",
        choices=["minimal", "docs"],
        help="Built-in scaffold profile",
    )
    init_parser.add_argument(
        "--profile-file",
        type=Path,
        default=None,
        help="JSON file describing custom scaffold profile",
    )
    init_parser.add_argument(
        "--with-examples",
        action="store_true",
        help="Add example command packages (issue/task)",
    )

    list_parser = subparsers.add_parser("list", help="List discovered commands")
    list_parser.add_argument("--all", action="store_true", help="Include invalid/conflicting commands")

    subparsers.add_parser("doctor", help="Validate command registry and report issues")

    doc_parser = subparsers.add_parser("doc", help="Show built-in documentation")
    doc_subparsers = doc_parser.add_subparsers(dest="doc_action", required=True)
    doc_subparsers.add_parser("list", help="List built-in documents")
    doc_show_parser = doc_subparsers.add_parser("show", help="Print a built-in document")
    doc_show_parser.add_argument("name", help="Document name")
    doc_path_parser = doc_subparsers.add_parser("path", help="Print the path to a built-in document")
    doc_path_parser.add_argument("name", help="Document name")

    new_parser = subparsers.add_parser("new", help="Generate assets from a command package")
    new_parser.add_argument("command_name", help="Command name to execute")
    new_parser.add_argument("pairs", nargs="*", help="Input values as key=value")
    new_parser.add_argument(
        "--json",
        dest="json_input",
        default=None,
        help="JSON object containing input values",
    )
    new_parser.add_argument(
        "--json-file",
        type=Path,
        default=None,
        help="Path to a JSON file containing input values",
    )
    new_parser.add_argument(
        "--set",
        dest="set_values",
        action="append",
        default=[],
        help="Additional input values as key=value",
    )
    new_parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="Prompt for missing input values",
    )
    new_parser.add_argument(
        "--no-input",
        action="store_true",
        help="Disable all interactive prompts",
    )
    new_parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="Show what would be generated without creating files",
    )
    new_parser.add_argument(
        "--conflict",
        choices=sorted(VALID_CONFLICT_POLICIES),
        default=None,
        help="Override conflict handling policy",
    )

    return parser


def _print_registry(registry, include_all: bool) -> int:
    if registry.commands:
        print(f"Project root: {registry.root}")
        print("Available commands:")
        for name in sorted(registry.commands):
            command = registry.commands[name]
            desc = f" - {command.description}" if command.description else ""
            print(f"  - {name}{desc}")
    else:
        print(f"Project root: {registry.root}")
        print("No available commands found.")

    if include_all:
        if registry.invalid:
            print("\nInvalid command packages:")
            for issue in registry.invalid:
                print(f"  - {issue.name}: {issue.message}")
        if registry.conflicts:
            print("\nConflicting command packages (disabled):")
            for issue in registry.conflicts:
                print(f"  - {issue.name}: {issue.message}")

    return 0


def _run_init(args: argparse.Namespace) -> int:
    report = initialize_workspace(
        Path.cwd(),
        profile=args.profile,
        profile_file=args.profile_file,
        with_examples=bool(args.with_examples),
    )

    print("Initialized .sprout workspace")
    if report.created:
        print("Created:")
        for path in report.created:
            print(f"  + {path}")
    if report.skipped:
        print("Skipped (already exists):")
        for path in report.skipped:
            print(f"  = {path}")
    for note in report.notes:
        print(f"Note: {note}")

    return 0


def _run_list(args: argparse.Namespace) -> int:
    registry = load_registry(Path.cwd())
    return _print_registry(registry, include_all=bool(args.all))


def _run_doctor() -> int:
    registry = load_registry(Path.cwd())

    print(f"Project root: {registry.root}")
    print(f"Config: conflict={registry.config.conflict}")
    print(f"Valid commands: {len(registry.commands)}")

    if registry.invalid:
        print("\nInvalid command packages:")
        for issue in registry.invalid:
            print(f"  - {issue.name}: {issue.message}")

    if registry.conflicts:
        print("\nConflicting command packages (disabled):")
        for issue in registry.conflicts:
            print(f"  - {issue.name}: {issue.message}")

    # Template validation
    template_issues = []
    for command in registry.commands.values():
        issues = validate_template_variables(command)
        template_issues.extend(issues)

    if template_issues:
        print("\nTemplate validation issues:")
        for issue in template_issues:
            print(f"  - {issue.command_name}/{issue.template_path}: {issue.message}")

    if registry.invalid or registry.conflicts or template_issues:
        return 1

    print("OK")
    return 0


def _get_builtin_doc(name: str) -> Path:
    docs = _builtin_docs()
    if name not in docs:
        available = ', '.join(sorted(docs))
        raise ValidationError(f"Unknown document '{name}'. Available: {available}")

    path = docs[name]
    if not path.exists():
        raise ValidationError(f"Built-in document not found: {name}")
    return path


def _run_doc(args: argparse.Namespace) -> int:
    if args.doc_action == 'list':
        print('Built-in documents:')
        for name in sorted(_builtin_docs()):
            print(f'  - {name}')
        return 0

    path = _get_builtin_doc(args.name)
    if args.doc_action == 'path':
        print(path)
        return 0
    if args.doc_action == 'show':
        print(path.read_text(encoding='utf-8'), end='')
        return 0

    raise ValidationError(f"Unknown doc action: {args.doc_action}")


def _is_tty_session() -> bool:
    return bool(sys.stdin.isatty() and sys.stdout.isatty())


def _read_confirmation(message: str) -> bool:
    answer = input(message).strip().lower()
    if answer in {"", "y", "yes"}:
        return True
    if answer in {"n", "no", "q", "quit", "exit"}:
        return False
    print("Please answer y/yes or n/no.")
    return _read_confirmation(message)


def _build_input_sources(args: argparse.Namespace) -> dict[str, Any]:
    base: dict[str, Any] = {}
    if args.json_input is not None and args.json_file is not None:
        raise ValidationError("Use either --json or --json-file, not both")
    if args.json_input is not None:
        base = parse_json_input(args.json_input)
    elif args.json_file is not None:
        base = load_json_input_file(args.json_file)

    pair_values = parse_key_value_pairs(list(args.pairs))
    set_values = parse_key_value_pairs(list(args.set_values))
    merged = merge_input_sources(base, pair_values)
    return merge_input_sources(merged, set_values)


def _print_missing_input_guidance(command, missing_specs) -> None:
    names = ", ".join(spec.name for spec in missing_specs)
    print(f"Missing required inputs: {names}", file=sys.stderr)
    print("Required fields:", file=sys.stderr)
    for spec in missing_specs:
        detail = spec.description or "No description provided."
        print(f"  - {spec.name}: {detail}", file=sys.stderr)
    print(f"Hint: run `sprout new {command.name} -i` to fill inputs interactively.", file=sys.stderr)
    print(
        f"Hint: or pass structured input with `sprout new {command.name} --json '{{\"{missing_specs[0].name}\":\"value\"}}'`.",
        file=sys.stderr,
    )


def _print_interactive_summary(command, values: dict[str, Any], policy: str, plan, actions, root: Path) -> None:
    print("Interactive summary")
    print(f"Command: {command.name}")
    print("Inputs:")
    for spec in command.inputs:
        if spec.name in values:
            print(f"  - {spec.name} = {values[spec.name]}")
    print(f"Conflict policy: {policy}")
    print("Planned outputs:")
    for item in plan:
        try:
            rel = item.final_path.relative_to(root)
        except ValueError:
            rel = item.final_path
        print(f"  - {item.action.upper()} {rel}")
    if actions:
        print("Planned actions:")
        for action in actions:
            cwd = ''
            if action.cwd is not None:
                try:
                    cwd_value = action.cwd.relative_to(root)
                except ValueError:
                    cwd_value = action.cwd
                cwd = f" (cwd={cwd_value})"
            print(f"  - {action.mode.upper()} {action.command_display}{cwd}")


def _run_new(args: argparse.Namespace) -> int:
    registry = load_registry(Path.cwd())

    if args.command_name not in registry.commands:
        print(f"Command not available: {args.command_name}", file=sys.stderr)
        suggestions = suggest_command_names(args.command_name, sorted(registry.commands.keys()))
        if suggestions:
            print(f"Did you mean: {', '.join(suggestions)}", file=sys.stderr)

        conflicting = [issue for issue in registry.conflicts if issue.name == args.command_name]
        invalid = [issue for issue in registry.invalid if issue.name == args.command_name]

        for issue in conflicting:
            print(f"Conflict: {issue.message}", file=sys.stderr)
        for issue in invalid:
            print(f"Invalid: {issue.message}", file=sys.stderr)

        if registry.commands:
            print("Available commands:", file=sys.stderr)
            for name in sorted(registry.commands):
                command = registry.commands[name]
                desc = f": {command.description}" if command.description else ""
                print(f"  - {name}{desc}", file=sys.stderr)
        else:
            print("Available commands: <none>", file=sys.stderr)
        print("Hint: run `sprout list` to inspect all commands.", file=sys.stderr)
        return 1

    command = registry.commands[args.command_name]
    provided = _build_input_sources(args)

    if args.interactive and not _is_tty_session():
        raise ValidationError("Interactive mode requires a TTY")

    missing_specs = find_missing_required_inputs(command, provided)
    interactive_mode = bool(args.interactive)

    if missing_specs and not interactive_mode:
        _print_missing_input_guidance(command, missing_specs)
        if args.no_input:
            return 1
        if _is_tty_session():
            if not _read_confirmation("Enter interactive mode? [Y/n] "):
                print("Cancelled. No files were created.", file=sys.stderr)
                return 1
            interactive_mode = True
        else:
            return 1

    values = collect_inputs(
        command,
        provided,
        interactive=interactive_mode,
    )
    context = build_variable_context(values)

    policy = effective_conflict_policy(command, registry.config, args.conflict)
    plan = build_generation_plan(command, registry.root, context, policy)
    preview_results = apply_generation_plan(plan, registry.root, dry_run=True)
    planned_actions = plan_post_actions(command, registry.root, context, preview_results)

    if interactive_mode:
        _print_interactive_summary(command, values, policy, plan, planned_actions, registry.root)
        if not _read_confirmation("Proceed? [Y/n] "):
            print("Cancelled. No files were created.", file=sys.stderr)
            return 1

    dry_run = bool(getattr(args, "dry_run", False))
    results = preview_results if dry_run else apply_generation_plan(plan, registry.root, dry_run=False)

    prefix = "[DRY-RUN] " if dry_run else ""
    print(f"{prefix}Executed command: {command.name}")
    print(f"{prefix}Conflict policy: {policy}")

    for result in results:
        path = result.final_path
        try:
            rel = path.relative_to(registry.root)
        except ValueError:
            rel = path

        action = result.action
        if action == "rename":
            print(f"{prefix}  ~ RENAMED -> {rel}")
        elif action == "overwrite":
            print(f"{prefix}  ! OVERWRITE {rel}")
        elif action == "skip":
            print(f"{prefix}  - SKIP {rel}")
        elif action == "reuse":
            print(f"{prefix}  = REUSE {rel}")
        else:
            print(f"{prefix}  + CREATE {rel}")

    for planned_action in planned_actions:
        cwd = ""
        if planned_action.cwd is not None:
            try:
                cwd_value = planned_action.cwd.relative_to(registry.root)
            except ValueError:
                cwd_value = planned_action.cwd
            cwd = f" (cwd={cwd_value})"
        print(f"{prefix}  > ACTION [{command.actions[planned_action.index].phase}] {planned_action.command_display}{cwd}")

    execute_actions(planned_actions, dry_run=dry_run)
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "init":
            return _run_init(args)
        if args.command == "list":
            return _run_list(args)
        if args.command == "doctor":
            return _run_doctor()
        if args.command == "doc":
            return _run_doc(args)
        if args.command == "new":
            return _run_new(args)

        parser.print_help()
        return 1

    except UserAbortError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except (DiscoveryError, ValidationError, GenerationError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
