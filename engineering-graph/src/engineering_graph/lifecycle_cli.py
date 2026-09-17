from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .config import load_settings
from .lifecycle import assess_lifecycle, collect_lifecycle_evidence


def _settings(args: argparse.Namespace):
    repo_root = (
        Path(args.repo_root).resolve()
        if getattr(args, "repo_root", None)
        else None
    )
    return load_settings(repo_root=repo_root)


def _root(args: argparse.Namespace) -> Path | None:
    value = getattr(args, "execution_root", None)
    return Path(value).resolve() if value else None


def _json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, default=str)


def command_lifecycle_status(args: argparse.Namespace) -> int:
    settings = _settings(args)
    gates = Path(args.human_gates).resolve() if args.human_gates else None
    evidence = collect_lifecycle_evidence(
        settings,
        args.task,
        human_gates_path=gates,
        root_override=_root(args),
        inspect_pr=not args.no_pr_inspect,
        base_branch=args.base,
    )
    assessment = assess_lifecycle(evidence)
    if args.json:
        print(_json(assessment.to_dict()))
    else:
        print(
            f"Lifecycle {assessment.task_id}: phase={assessment.phase} "
            f"next={assessment.next_action}"
        )
        print(
            f"  repo: {assessment.repository} "
            f"head={assessment.head_sha} base={evidence.base_branch}"
        )
        publication = evidence.publication
        if publication is not None and publication.pr_url:
            print(f"  PR: {publication.pr_url}")
        if assessment.blockers:
            for blocker in assessment.blockers:
                print(f"  blocker[{blocker.code}]: {blocker.detail}")
        unresolved = assessment.to_dict()["continuation"][
            "unresolvedHumanAsyncGates"
        ]
        for gate in unresolved:
            print(
                f"  human[{gate['gateId']}]: "
                f"status={gate['status']} fresh={gate['fresh']}"
            )
    return 1 if assessment.phase == "blocked" else 0


def register_lifecycle_subcommands(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    status = subparsers.add_parser(
        "lifecycle-status",
        help=(
            "Read-only V10 lifecycle projection across V3-V9 evidence "
            "and Human Async Gates"
        ),
    )
    status.add_argument("--task", required=True)
    status.add_argument("--base", default="master")
    status.add_argument("--execution-root")
    status.add_argument("--human-gates")
    status.add_argument("--no-pr-inspect", action="store_true")
    status.add_argument("--json", action="store_true")
    status.set_defaults(func=command_lifecycle_status)
