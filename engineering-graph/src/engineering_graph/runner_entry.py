from __future__ import annotations

import argparse
import sys
from typing import Sequence

from . import cli as legacy_cli
from .post_publication_cli import register_post_publication_subcommands
from .publisher_cli import register_publisher_subcommands
from .runner_cli import register_runner_subcommands
from .supervisor_cli import register_supervisor_subcommands
from .validation_cli import register_validation_subcommands

RUNNER_COMMANDS = frozenset({"runner-start", "runner-status", "runner-stop", "runner-logs"})
SUPERVISOR_COMMANDS = frozenset(
    {"supervisor-start", "supervisor-tick", "supervisor-status", "supervisor-stop"}
)
VALIDATION_COMMANDS = frozenset({"validation-run", "validation-status"})
PUBLISHER_COMMANDS = frozenset({"publication-run", "publication-resume", "publication-status"})
POST_PUBLICATION_COMMANDS = frozenset({"post-publication-status", "post-publication-finalize"})
LOCAL_COMMANDS = (
    RUNNER_COMMANDS
    | SUPERVISOR_COMMANDS
    | VALIDATION_COMMANDS
    | PUBLISHER_COMMANDS
    | POST_PUBLICATION_COMMANDS
)


def _command_token(argv: Sequence[str]) -> str | None:
    index = 0
    values = list(argv)
    while index < len(values):
        token = values[index]
        if token == "--repo-root":
            index += 2
            continue
        if token.startswith("--repo-root="):
            index += 1
            continue
        if token.startswith("-"):
            return None
        return token
    return None


def _runner_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="graph-engineering")
    parser.add_argument("--repo-root", help="Repository root (auto-discovered by default)")
    subparsers = parser.add_subparsers(dest="command", required=True)
    register_runner_subcommands(subparsers)
    register_supervisor_subcommands(subparsers)
    register_validation_subcommands(subparsers)
    register_publisher_subcommands(subparsers)
    register_post_publication_subcommands(subparsers)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    values = list(argv if argv is not None else sys.argv[1:])
    if _command_token(values) not in LOCAL_COMMANDS:
        return legacy_cli.main(values)
    parser = _runner_parser()
    args = parser.parse_args(values)
    try:
        return int(args.func(args))
    except KeyboardInterrupt:
        return 130
    except Exception as error:
        print(f"graph-engineering: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
