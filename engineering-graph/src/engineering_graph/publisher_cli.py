from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .config import load_settings
from .publisher import resume_publication, run_publication, status_publications


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
        f"Publication {record.publication_id}: task={record.task_id} status={record.status} "
        f"branch={record.branch} commit={record.commit_sha or '-'}"
    )
    if record.pr_url:
        print(f"  PR: {record.pr_url}")
    if record.failed_phase:
        print(f"  failure[{record.failed_phase}]: {record.error}")


def command_publication_run(args: argparse.Namespace) -> int:
    settings = _settings(args)
    record = run_publication(
        settings,
        args.task_id,
        args.validation,
        commit_message=args.commit_message,
        pr_title=args.pr_title,
        pr_body=args.pr_body,
        base_branch=args.base,
        root_override=_root(args),
    )
    if args.json:
        print(_json(record.to_dict()))
    else:
        _print_record(record)
    return 0 if record.status == "pr_opened" else 1


def command_publication_resume(args: argparse.Namespace) -> int:
    settings = _settings(args)
    record = resume_publication(settings, args.publication_id, root_override=_root(args))
    if args.json:
        print(_json(record.to_dict()))
    else:
        _print_record(record)
    return 0 if record.status == "pr_opened" else 1


def command_publication_status(args: argparse.Namespace) -> int:
    settings = _settings(args)
    records = status_publications(
        settings,
        task_id=args.task,
        validation_id=args.validation,
        publication_id=args.publication,
        root_override=_root(args),
    )
    if args.json:
        print(_json([record.to_dict() for record in records]))
    elif not records:
        print("No Git Publisher history.")
    else:
        for record in records:
            _print_record(record)
    return 0


def register_publisher_subcommands(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    run = subparsers.add_parser(
        "publication-run",
        help="Commit, push and open a PR for one exact passed V7 validation",
    )
    run.add_argument("task_id")
    run.add_argument("--validation", required=True)
    run.add_argument("--commit-message", required=True)
    run.add_argument("--pr-title", required=True)
    run.add_argument("--pr-body", default="")
    run.add_argument("--base", default="master")
    run.add_argument("--execution-root")
    run.add_argument("--json", action="store_true")
    run.set_defaults(func=command_publication_run)

    resume = subparsers.add_parser(
        "publication-resume",
        help="Resume a partial V8 publication without creating a duplicate commit",
    )
    resume.add_argument("publication_id")
    resume.add_argument("--execution-root")
    resume.add_argument("--json", action="store_true")
    resume.set_defaults(func=command_publication_resume)

    status = subparsers.add_parser(
        "publication-status",
        help="Inspect disposable Git Publisher evidence without mutating Git",
    )
    status.add_argument("--task")
    status.add_argument("--validation")
    status.add_argument("--publication")
    status.add_argument("--execution-root")
    status.add_argument("--json", action="store_true")
    status.set_defaults(func=command_publication_status)
