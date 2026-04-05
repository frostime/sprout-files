from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from . import __version__
from .core import (
    VALID_CONFLICT_POLICIES,
    apply_generation_plan,
    build_generation_plan,
    build_variable_context,
    collect_inputs,
    effective_conflict_policy,
    load_registry,
    parse_key_value_pairs,
)
from .models import DiscoveryError, GenerationError, ValidationError
from .scaffold import BUILTIN_PROFILES, initialize_workspace


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sprout", description="Template-driven project generator")
    parser.add_argument("--version", action="version", version=f"sprout {__version__}")

    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Initialize .sprout workspace")
    init_parser.add_argument(
        "--profile",
        default="minimal",
        choices=sorted(BUILTIN_PROFILES.keys()),
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
        help="Add example command packages (issue/change)",
    )

    list_parser = subparsers.add_parser("list", help="List discovered commands")
    list_parser.add_argument("--all", action="store_true", help="Include invalid/conflicting commands")

    subparsers.add_parser("doctor", help="Validate command registry and report issues")

    new_parser = subparsers.add_parser("new", help="Generate assets from a command package")
    new_parser.add_argument("command_name", help="Command name to execute")
    new_parser.add_argument("pairs", nargs="*", help="Input values as key=value")
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

    if registry.invalid or registry.conflicts:
        return 1

    print("OK")
    return 0


def _run_new(args: argparse.Namespace) -> int:
    registry = load_registry(Path.cwd())

    if args.command_name not in registry.commands:
        print(f"Command not available: {args.command_name}", file=sys.stderr)

        conflicting = [issue for issue in registry.conflicts if issue.name == args.command_name]
        invalid = [issue for issue in registry.invalid if issue.name == args.command_name]

        for issue in conflicting:
            print(f"Conflict: {issue.message}", file=sys.stderr)
        for issue in invalid:
            print(f"Invalid: {issue.message}", file=sys.stderr)

        available = ", ".join(sorted(registry.commands.keys())) or "<none>"
        print(f"Available commands: {available}", file=sys.stderr)
        return 1

    command = registry.commands[args.command_name]
    provided_pairs = parse_key_value_pairs(list(args.pairs) + list(args.set_values))

    values = collect_inputs(
        command,
        provided_pairs,
        interactive=bool(args.interactive),
    )
    context = build_variable_context(values)

    policy = effective_conflict_policy(command, registry.config, args.conflict)
    plan = build_generation_plan(command, registry.root, context, policy)
    results = apply_generation_plan(plan, registry.root)

    print(f"Executed command: {command.name}")
    print(f"Conflict policy: {policy}")

    for result in results:
        path = result.final_path
        try:
            rel = path.relative_to(registry.root)
        except ValueError:
            rel = path

        action = result.action
        if action == "rename":
            print(f"  ~ RENAMED -> {rel}")
        elif action == "overwrite":
            print(f"  ! OVERWRITE {rel}")
        elif action == "skip":
            print(f"  - SKIP {rel}")
        else:
            print(f"  + CREATE {rel}")

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
        if args.command == "new":
            return _run_new(args)

        parser.print_help()
        return 1

    except (DiscoveryError, ValidationError, GenerationError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
