from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import signal
import subprocess
from typing import Sequence

RESULT_VERSION = "1"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _atomic_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    temporary = path.with_name(f".{path.name}.tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        handle.write(rendered)
        handle.flush()
        os.fsync(handle.fileno())
    temporary.replace(path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="engineering-graph-runner-child")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--result", required=True)
    parser.add_argument("--stdout", required=True)
    parser.add_argument("--stderr", required=True)
    parser.add_argument("--argv-json", required=True)
    parser.add_argument("--stdin-file")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    raw = json.loads(args.argv_json)
    if not isinstance(raw, list) or not raw or not all(isinstance(value, str) for value in raw):
        raise SystemExit("runner child requires a non-empty JSON argv array")
    command = [str(value) for value in raw]
    stdin_data = Path(args.stdin_file).read_bytes() if args.stdin_file else None
    stdout_path = Path(args.stdout)
    stderr_path = Path(args.stderr)
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    stderr_path.parent.mkdir(parents=True, exist_ok=True)

    child: subprocess.Popen[bytes] | None = None
    stop_requested = False

    def request_stop(_signum: int, _frame: object) -> None:
        nonlocal stop_requested
        stop_requested = True
        if child is not None and child.poll() is None:
            try:
                child.terminate()
            except ProcessLookupError:
                pass

    signal.signal(signal.SIGTERM, request_stop)

    exit_code: int
    with stdout_path.open("ab", buffering=0) as stdout_handle, stderr_path.open("ab", buffering=0) as stderr_handle:
        try:
            child = subprocess.Popen(
                command,
                stdin=subprocess.PIPE if stdin_data is not None else subprocess.DEVNULL,
                stdout=stdout_handle,
                stderr=stderr_handle,
                shell=False,
            )
            child.communicate(input=stdin_data)
            exit_code = int(child.returncode if child.returncode is not None else 1)
        except OSError as error:
            stderr_handle.write(
                f"runner child failed to execute argv: {error}\n".encode("utf-8", errors="replace")
            )
            exit_code = 127

    # A graceful stop still records the child exit so a detached caller can reconcile
    # terminal state without mistaking a short-lived zombie wrapper for a running process.
    _atomic_json(
        Path(args.result),
        {
            "resultVersion": RESULT_VERSION,
            "runId": args.run_id,
            "exitCode": exit_code,
            "finishedAt": _utc_now(),
        },
    )
    return exit_code if not stop_requested else (exit_code or 143)


if __name__ == "__main__":
    raise SystemExit(main())
