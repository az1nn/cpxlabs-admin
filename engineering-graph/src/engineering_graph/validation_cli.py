from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .config import load_settings
from .validation import run_validation, status_validations


def _settings(args: argparse.Namespace):
    repo_root = Path(args.repo_root).resolve() if getattr(args, "repo_root", None) else None
    return load_settings(repo_root=repo_root)


def _root(args: argparse.Namespace) -> Path | None:
    value = getattr(args, "execution_root", None)
    return Path(value).resolve() if value else None


def _json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, default=str)


def _print_record(record) -> None:
    print(
        f"Validation {record.validation_id}: task={record.task_id} status={record.status} "
        f"commands={len(record.commands)} stable={record.workspace_stable}"
    )
    for result in record.commands:
        code = "-" if result.exit_code is None else str(result.exit_code)
        print(f"  [{result.index}] {result.status} exit={code}: {result.command}")


def command_validation_run(args: argparse.Namespace) -> int:
    settings = _settings(args)
    record = run_validation(settings, args.task_id, root_override=_root(args))
    if args.json:
        print(_json(record.to_dict()))
    else:
        _print_record(record)
    return 0 if record.status == "passed" else 1


def command_validation_status(args: argparse.Namespace) -> int:
    settings = _settings(args)
    records = status_validations(
        settings,
        task_id=args.task,
        validation_id=args.validation,
        root_override=_root(args),
    )
    if args.json:
        print(_json([record.to_dict() for record in records]))
    elif not records:
        print("No Agent Validator history.")
    else:
        for record in records:
            _print_record(record)
    return 0


def register_validation_subcommands(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    run = subparsers.add_parser(
        "validation-run",
        help="Execute the active allocation's frozen validation commands after successful V5 execution",
    )
    run.add_argument("task_id")
    run.add_argument("--execution-root")
    run.add_argument("--json", action="store_true")
    run.set_defaults(func=command_validation_run)

    status = subparsers.add_parser(
        "validation-status",
        help="Inspect disposable Agent Validator evidence without executing commands",
    )
    status.add_argument("--task")
    status.add_argument("--validation")
    status.add_argument("--execution-root")
    status.add_argument("--json", action="store_true")
    status.set_defaults(func=command_validation_status)
