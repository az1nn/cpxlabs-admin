from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .config import load_settings
from .post_publication import finalize_post_publication, reconcile_post_publication


def _settings(args: argparse.Namespace):
    repo_root = Path(args.repo_root).resolve() if getattr(args, "repo_root", None) else None
    return load_settings(repo_root=repo_root)


def _root(args: argparse.Namespace) -> Path | None:
    value = getattr(args, "execution_root", None)
    return Path(value).resolve() if value else None


def _json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, default=str)


def command_post_publication_status(args: argparse.Namespace) -> int:
    settings = _settings(args)
    result = reconcile_post_publication(settings, args.publication, root_override=_root(args))
    if args.json:
        print(_json(result.to_dict()))
    else:
        print(
            f"Post-publication {result.publication_id}: task={result.task_id} "
            f"merged={result.pr_merged} canonicalComplete={result.canonical_task_completed} "
            f"leaseActive={result.lease_active} finalizable={result.finalizable}"
        )
        print(f"  PR: {result.pr_url}")
        print(f"  base: {result.base_branch}@{result.base_revision or '-'}")
        if result.blockers:
            for blocker in result.blockers:
                print(f"  blocker: {blocker}")
    return 0 if result.finalizable or result.already_finalized else 1


def command_post_publication_finalize(args: argparse.Namespace) -> int:
    settings = _settings(args)
    receipt = finalize_post_publication(
        settings,
        args.publication,
        release=args.release_lease,
        remove=args.remove_worktree,
        root_override=_root(args),
    )
    if args.json:
        print(_json(receipt.to_dict()))
    else:
        print(
            f"Post-publication {receipt.publication_id}: status={receipt.status} "
            f"leaseReleased={receipt.lease_released} worktreeRemoved={receipt.worktree_removed}"
        )
        print(f"  PR: {receipt.pr_url}")
        print(f"  merge: {receipt.merge_commit_sha}")
        if receipt.block_reason:
            print(f"  blocker: {receipt.block_reason}")
    return 0 if receipt.status == "finalized" else 1


def register_post_publication_subcommands(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    status = subparsers.add_parser(
        "post-publication-status",
        help="Reconcile one V8 publication against merged base and canonical Task state",
    )
    status.add_argument("--publication", required=True)
    status.add_argument("--execution-root")
    status.add_argument("--json", action="store_true")
    status.set_defaults(func=command_post_publication_status)

    finalize = subparsers.add_parser(
        "post-publication-finalize",
        help="Explicitly release the matching lease and optionally remove its clean worktree",
    )
    finalize.add_argument("--publication", required=True)
    finalize.add_argument("--release-lease", action="store_true")
    finalize.add_argument("--remove-worktree", action="store_true")
    finalize.add_argument("--execution-root")
    finalize.add_argument("--json", action="store_true")
    finalize.set_defaults(func=command_post_publication_finalize)
