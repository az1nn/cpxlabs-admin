from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .config import load_settings
from .runner import read_run_logs, start_run, status_runs, stop_run


def _settings(args: argparse.Namespace):
    repo_root = Path(args.repo_root).resolve() if getattr(args, "repo_root", None) else None
    return load_settings(repo_root=repo_root)


def _root(args: argparse.Namespace) -> Path | None:
    value = getattr(args, "execution_root", None)
    return Path(value).resolve() if value else None


def _json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, default=str)


def command_runner_start(args: argparse.Namespace) -> int:
    settings = _settings(args)
    run = start_run(
        settings,
        args.task_id,
        args.command,
        stdin_handoff=args.stdin_handoff,
        root_override=_root(args),
    )
    if args.json:
        print(_json(run.to_dict()))
    else:
        print(
            f"Started runner {run.run_id} for {run.task_id}: "
            f"pid={run.pid} cwd={run.worktree_path}"
        )
    return 0


def command_runner_status(args: argparse.Namespace) -> int:
    settings = _settings(args)
    runs = status_runs(
        settings,
        task_id=args.task,
        root_override=_root(args),
    )
    payload = [run.to_dict() for run in runs]
    if args.json:
        print(_json(payload))
    elif not runs:
        print("No Agent Runner history.")
    else:
        for run in runs:
            exit_text = "-" if run.exit_code is None else str(run.exit_code)
            print(
                f"{run.task_id}: run={run.run_id} status={run.status} "
                f"pid={run.pid or '-'} exit={exit_text}"
            )
    return 0


def command_runner_stop(args: argparse.Namespace) -> int:
    settings = _settings(args)
    run = stop_run(
        settings,
        args.task_id,
        root_override=_root(args),
        timeout_seconds=args.timeout,
        force=args.force,
    )
    if args.json:
        print(_json(run.to_dict()))
    else:
        print(
            f"Runner {run.run_id} for {run.task_id}: "
            f"status={run.status} exit={run.exit_code}"
        )
    return 0


def command_runner_logs(args: argparse.Namespace) -> int:
    settings = _settings(args)
    payload = read_run_logs(
        settings,
        args.task_id,
        stream=args.stream,
        max_bytes=args.max_bytes,
        root_override=_root(args),
    )
    if args.json:
        print(_json(payload))
    else:
        if args.stream == "both":
            print("--- stdout ---")
            print(payload.get("stdout", ""), end="" if payload.get("stdout", "").endswith("\n") else "\n")
            print("--- stderr ---")
            print(payload.get("stderr", ""), end="" if payload.get("stderr", "").endswith("\n") else "\n")
        else:
            value = payload.get(args.stream, "")
            print(value, end="" if value.endswith("\n") else "\n")
    return 0


def register_runner_subcommands(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    start = subparsers.add_parser(
        "runner-start",
        help="Start an agent process for an active V3 execution allocation",
    )
    start.add_argument("task_id")
    start.add_argument("--stdin-handoff", action="store_true")
    start.add_argument("--execution-root")
    start.add_argument("--json", action="store_true")
    start.add_argument(
        "--command",
        nargs=argparse.REMAINDER,
        required=True,
        help="Literal argv remainder; place runner options before --command",
    )
    start.set_defaults(func=command_runner_start)

    status = subparsers.add_parser(
        "runner-status",
        help="Reconcile and inspect local Agent Runner process state",
    )
    status.add_argument("--task")
    status.add_argument("--execution-root")
    status.add_argument("--json", action="store_true")
    status.set_defaults(func=command_runner_status)

    stop = subparsers.add_parser(
        "runner-stop",
        help="Safely stop a verified Agent Runner process group",
    )
    stop.add_argument("task_id")
    stop.add_argument("--execution-root")
    stop.add_argument("--timeout", type=float, default=5.0)
    stop.add_argument("--force", action="store_true")
    stop.add_argument("--json", action="store_true")
    stop.set_defaults(func=command_runner_stop)

    logs = subparsers.add_parser(
        "runner-logs",
        help="Read bounded stdout/stderr from the latest run for a task",
    )
    logs.add_argument("task_id")
    logs.add_argument("--stream", choices=("stdout", "stderr", "both"), default="stdout")
    logs.add_argument("--max-bytes", type=int, default=65536)
    logs.add_argument("--execution-root")
    logs.add_argument("--json", action="store_true")
    logs.set_defaults(func=command_runner_logs)
