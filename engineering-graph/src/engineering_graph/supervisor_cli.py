from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .config import load_settings
from .execution import load_execution_manifest
from .supervisor import (
    start_supervisor_job,
    status_supervisor_jobs,
    stop_supervisor_job,
    supervisor_tick,
)


def _settings(args: argparse.Namespace):
    repo_root = Path(args.repo_root).resolve() if getattr(args, "repo_root", None) else None
    return load_settings(repo_root=repo_root)


def _root(args: argparse.Namespace) -> Path | None:
    value = getattr(args, "execution_root", None)
    return Path(value).resolve() if value else None


def _json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, default=str)


def _print_job(job) -> None:
    states = ", ".join(f"{task.task_id}={task.status}" for task in job.tasks)
    print(
        f"Supervisor {job.job_id}: status={job.status} wave={job.wave} "
        f"parallel={job.max_parallel} attempts={job.max_attempts}"
    )
    print(states)


def command_supervisor_start(args: argparse.Namespace) -> int:
    settings = _settings(args)
    manifest_path = Path(args.manifest).resolve()
    manifest = load_execution_manifest(manifest_path)
    job = start_supervisor_job(
        settings,
        manifest,
        manifest_path,
        args.wave,
        args.command,
        max_parallel=args.max_parallel,
        max_attempts=args.max_attempts,
        stdin_handoff=args.stdin_handoff,
        root_override=_root(args),
    )
    if args.json:
        print(_json(job.to_dict()))
    else:
        _print_job(job)
    return 0


def command_supervisor_tick(args: argparse.Namespace) -> int:
    settings = _settings(args)
    job = supervisor_tick(settings, args.job_id, root_override=_root(args))
    if args.json:
        print(_json(job.to_dict()))
    else:
        _print_job(job)
    return 0


def command_supervisor_status(args: argparse.Namespace) -> int:
    settings = _settings(args)
    jobs = status_supervisor_jobs(
        settings,
        job_id=args.job,
        root_override=_root(args),
    )
    if args.json:
        print(_json([job.to_dict() for job in jobs]))
    elif not jobs:
        print("No Agent Supervisor history.")
    else:
        for job in jobs:
            _print_job(job)
    return 0


def command_supervisor_stop(args: argparse.Namespace) -> int:
    settings = _settings(args)
    job = stop_supervisor_job(
        settings,
        args.job_id,
        root_override=_root(args),
        timeout_seconds=args.timeout,
        force=args.force,
    )
    if args.json:
        print(_json(job.to_dict()))
    else:
        _print_job(job)
    return 0


def register_supervisor_subcommands(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    start = subparsers.add_parser(
        "supervisor-start",
        help="Create and tick a local supervisor for one prepared execution wave",
    )
    start.add_argument("manifest")
    start.add_argument("--wave", type=int, required=True)
    start.add_argument("--max-parallel", type=int, default=1)
    start.add_argument("--max-attempts", type=int, default=1)
    start.add_argument("--stdin-handoff", action="store_true")
    start.add_argument("--execution-root")
    start.add_argument("--json", action="store_true")
    start.add_argument(
        "--command",
        nargs=argparse.REMAINDER,
        required=True,
        help="Literal argv remainder for every supervised V5 run",
    )
    start.set_defaults(func=command_supervisor_start)

    tick = subparsers.add_parser(
        "supervisor-tick",
        help="Reconcile one supervisor job and launch eligible work within its bounds",
    )
    tick.add_argument("job_id")
    tick.add_argument("--execution-root")
    tick.add_argument("--json", action="store_true")
    tick.set_defaults(func=command_supervisor_tick)

    status = subparsers.add_parser(
        "supervisor-status",
        help="Inspect supervisor state without launching new work",
    )
    status.add_argument("--job")
    status.add_argument("--execution-root")
    status.add_argument("--json", action="store_true")
    status.set_defaults(func=command_supervisor_status)

    stop = subparsers.add_parser(
        "supervisor-stop",
        help="Stop only the current V5 runs owned by one supervisor job",
    )
    stop.add_argument("job_id")
    stop.add_argument("--execution-root")
    stop.add_argument("--timeout", type=float, default=5.0)
    stop.add_argument("--force", action="store_true")
    stop.add_argument("--json", action="store_true")
    stop.set_defaults(func=command_supervisor_stop)
