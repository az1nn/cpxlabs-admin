from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Sequence

from .agent_adapters import SUPPORTED_AGENTS, render_agent_handoff
from .config import ContextBudget, load_settings
from .context import build_context, write_context
from .context_batch import generate_context_packages
from .context_validation import inspect_freshness, load_context_package
from .execution import load_execution_manifest, write_execution_manifest
from .orchestrator import (
    build_manifest_from_store,
    execution_status,
    prepare_execution,
    release_execution,
)
from .planner import build_execution_plan, load_tasks_from_store
from .schema import validate_schema_definitions
from .store import GraphStore
from .sync import synchronize
from .validator import has_errors, validate_graph


def _json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, default=str)


def _print_rows(rows: list[dict[str, Any]]) -> None:
    if not rows:
        print("No results.")
        return
    for row in rows:
        print(" | ".join(f"{key}={value}" for key, value in row.items()))


def _settings(args: argparse.Namespace):
    repo_root = Path(args.repo_root).resolve() if getattr(args, "repo_root", None) else None
    return load_settings(repo_root=repo_root)


def _with_store(args: argparse.Namespace):
    settings = _settings(args)
    return settings, GraphStore(settings)


def _context_budget(args: argparse.Namespace, settings) -> ContextBudget:
    return ContextBudget(
        max_depth=args.depth if getattr(args, "depth", None) is not None else settings.context.max_depth,
        max_nodes=args.max_nodes if getattr(args, "max_nodes", None) is not None else settings.context.max_nodes,
        max_bytes=args.max_bytes if getattr(args, "max_bytes", None) is not None else settings.context.max_bytes,
    )


def command_doctor(args: argparse.Namespace) -> int:
    settings, store = _with_store(args)
    try:
        validate_schema_definitions(settings)
        if args.wait > 0:
            store.wait_until_ready(args.wait)
        else:
            store.verify_connectivity()
        records = store.run("RETURN 1 AS ok")
        print(
            f"Engineering Graph OK: repo={settings.repository_id} "
            f"neo4j={settings.neo4j.uri} database={settings.neo4j.database} "
            f"query={records[0]['ok'] if records else 'unknown'}"
        )
        return 0
    finally:
        store.close()


def command_schema(args: argparse.Namespace) -> int:
    settings, store = _with_store(args)
    try:
        store.initialize_schema()
        print("Engineering Graph schema initialized.")
        return 0
    finally:
        store.close()


def command_sync(args: argparse.Namespace) -> int:
    settings = _settings(args)
    event = Path(args.github_event).resolve() if args.github_event else None
    result = synchronize(settings, github_event_path=event)
    if args.json:
        print(_json(result.to_dict()))
    else:
        print(f"Synced {result.repository} @ {result.source_revision}")
        print("Nodes:", ", ".join(f"{name}={count}" for name, count in result.node_counts.items()))
        print(
            "Relationships:",
            ", ".join(f"{name}={count}" for name, count in result.relationship_counts.items()),
        )
        for warning in result.extraction_warnings:
            print(f"WARNING {warning['code']}: {warning['message']}", file=sys.stderr)
    return 0


def command_validate(args: argparse.Namespace) -> int:
    settings, store = _with_store(args)
    try:
        results = validate_graph(store, settings)
    finally:
        store.close()
    payload = [result.to_dict() for result in results]
    if args.json:
        print(_json(payload))
    elif not results:
        print("Graph validation passed with no findings.")
    else:
        for result in results:
            location = f" [{result.source_path}]" if result.source_path else ""
            print(f"{result.severity.upper()} {result.rule}: {result.entity}{location} — {result.message}")
        errors = sum(result.severity == "error" for result in results)
        warnings = sum(result.severity == "warning" for result in results)
        print(f"Validation findings: errors={errors}, warnings={warnings}")
    return 1 if has_errors(results) else 0


def command_impact(args: argparse.Namespace) -> int:
    settings, store = _with_store(args)
    try:
        rows = store.query_file(
            "impact.cypher",
            {
                "repository": settings.repository_id,
                "canonicalId": args.canonical_id,
                "depth": min(max(args.depth, 1), 5),
                "limit": min(max(args.limit, 1), 500),
            },
        )
    finally:
        store.close()
    if args.json:
        print(_json(rows))
    else:
        _print_rows(rows)
    return 0


def command_ready(args: argparse.Namespace) -> int:
    settings, store = _with_store(args)
    try:
        rows = store.query_file(
            "ready-tasks.cypher",
            {"repository": settings.repository_id, "specId": args.spec},
        )
    finally:
        store.close()
    if args.json:
        print(_json(rows))
    else:
        _print_rows(rows)
    return 0


def command_conflicts(args: argparse.Namespace) -> int:
    settings, store = _with_store(args)
    try:
        rows = store.query_file(
            "conflicts.cypher",
            {"repository": settings.repository_id, "specId": args.spec},
        )
    finally:
        store.close()
    if args.json:
        print(_json(rows))
    else:
        _print_rows(rows)
    return 0


def command_drift(args: argparse.Namespace) -> int:
    settings, store = _with_store(args)
    try:
        rows = store.query_file("drift.cypher", {"repository": settings.repository_id})
    finally:
        store.close()
    if args.json:
        print(_json(rows))
    else:
        _print_rows(rows)
    return 0


def command_context(args: argparse.Namespace) -> int:
    settings, store = _with_store(args)
    budget = _context_budget(args, settings)
    try:
        package = build_context(store, settings, args.task_id, budget)
    finally:
        store.close()
    rendered = write_context(
        package,
        args.format,
        Path(args.output).resolve() if args.output else None,
    )
    if not args.output:
        print(rendered)
    else:
        print(f"Context package written to {args.output}")
    return 0


def command_context_batch(args: argparse.Namespace) -> int:
    settings, store = _with_store(args)
    budget = _context_budget(args, settings)
    try:
        manifest = generate_context_packages(
            store,
            settings,
            spec_id=args.spec,
            explicit_task_ids=args.task or (),
            output_root=Path(args.output_root).resolve() if args.output_root else None,
            budget=budget,
        )
    finally:
        store.close()
    payload = manifest.to_dict()
    if args.json:
        print(_json(payload))
    else:
        print(
            f"Generated {payload['packageCount']} context package(s) for "
            f"{payload['repository']} @ {payload['sourceRevision']}"
        )
        for item in payload["tasks"]:
            print(
                f"{item['taskId']}: {item['directory']} "
                f"nodes={item['includedNodes']} truncated={item['truncatedNodes']} bytes={item['renderedBytes']}"
            )
    return 0


def command_context_validate(args: argparse.Namespace) -> int:
    settings = _settings(args)
    package = load_context_package(Path(args.package).resolve())
    report = inspect_freshness(
        package,
        settings.repo_root,
        expected_repository=settings.repository_id,
        strict=args.strict,
    )
    if args.json:
        print(_json(report.to_dict()))
    else:
        print(
            f"Context package {report.status}: package={report.package_revision} "
            f"current={report.current_revision or 'unknown'}"
        )
        for message in report.messages:
            print(f"- {message}")
    return 0 if report.valid else 1


def command_context_adapt(args: argparse.Namespace) -> int:
    package = load_context_package(Path(args.package).resolve())
    rendered = render_agent_handoff(package, args.agent, Path(args.package).name)
    if args.output:
        destination = Path(args.output).resolve()
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(rendered, encoding="utf-8")
        print(f"{args.agent} handoff written to {destination}")
    else:
        print(rendered)
    return 0


def command_waves(args: argparse.Namespace) -> int:
    settings, store = _with_store(args)
    try:
        tasks = load_tasks_from_store(store, settings.repository_id, args.spec)
    finally:
        store.close()
    plan = build_execution_plan(tasks)
    payload = plan.to_dict()
    if args.json:
        print(_json(payload))
    else:
        print("READY:", ", ".join(plan.ready) or "none")
        for task, blockers in plan.blocked:
            print(f"BLOCKED {task}: {', '.join(blockers)}")
        for cycle in plan.cycles:
            print(f"CYCLE: {' -> '.join(cycle)}", file=sys.stderr)
        for conflict in plan.conflicts:
            print(f"CONFLICT {conflict.left} <> {conflict.right}: {', '.join(conflict.artifacts)}")
        for index, wave in enumerate(plan.waves, start=1):
            print(f"WAVE {index}: {', '.join(wave)}")
    return 1 if plan.cycles else 0


def command_execution_plan(args: argparse.Namespace) -> int:
    settings, store = _with_store(args)
    try:
        manifest = build_manifest_from_store(
            store,
            settings,
            spec_id=args.spec,
            agent=args.agent,
        )
    finally:
        store.close()

    if args.output:
        destination = Path(args.output).resolve()
        write_execution_manifest(manifest, destination)
        if not args.json:
            print(f"Execution manifest written to {destination}")
    if args.json:
        print(_json(manifest.to_dict()))
    elif not args.output:
        print(f"Repository: {manifest.repository}")
        print(f"Source revision: {manifest.source_revision}")
        print("READY:", ", ".join(manifest.ready) or "none")
        for task, blockers in manifest.blocked:
            print(f"BLOCKED {task}: {', '.join(blockers)}")
        for cycle in manifest.cycles:
            print(f"CYCLE: {' -> '.join(cycle)}", file=sys.stderr)
        for conflict in manifest.conflicts:
            print(f"CONFLICT {conflict.left} <> {conflict.right}: {', '.join(conflict.artifacts)}")
        for wave in manifest.waves:
            print(f"WAVE {wave.index}: {', '.join(wave.tasks)}")
    return 1 if manifest.cycles else 0


def command_execution_prepare(args: argparse.Namespace) -> int:
    settings, store = _with_store(args)
    manifest = load_execution_manifest(Path(args.manifest).resolve())
    try:
        result = prepare_execution(
            store,
            settings,
            manifest,
            wave=args.wave,
            task_ids=args.task or (),
            root_override=Path(args.execution_root).resolve() if args.execution_root else None,
            dry_run=args.dry_run,
        )
    finally:
        store.close()

    payload = result.to_dict()
    if args.json:
        print(_json(payload))
    else:
        action = "Planned" if result.dry_run else "Prepared"
        print(f"{action} {payload['allocationCount']} execution allocation(s)")
        for allocation in result.allocations:
            print(
                f"{allocation.task_id}: branch={allocation.branch} "
                f"worktree={allocation.worktree_path} handoff={allocation.handoff_path}"
            )
    return 0


def command_execution_status(args: argparse.Namespace) -> int:
    settings = _settings(args)
    payload = execution_status(
        settings,
        root_override=Path(args.execution_root).resolve() if args.execution_root else None,
    )
    if args.json:
        print(_json(payload))
    else:
        print(f"Active execution leases: {payload['activeCount']}")
        for lease in payload["active"]:
            dirty = lease.get("dirty")
            dirty_text = "unknown" if dirty is None else ("dirty" if dirty else "clean")
            print(
                f"{lease['taskId']}: {lease['branch']} @ {lease['worktreePath']} "
                f"registered={lease['worktreeRegistered']} state={dirty_text}"
            )
    return 0


def command_execution_release(args: argparse.Namespace) -> int:
    settings = _settings(args)
    allocation = release_execution(
        settings,
        args.task_id,
        root_override=Path(args.execution_root).resolve() if args.execution_root else None,
        remove=args.remove_worktree,
        force=args.force,
    )
    if args.json:
        print(_json(allocation.to_dict()))
    else:
        print(
            f"Released {allocation.task_id}: branch={allocation.branch} "
            f"worktree={allocation.worktree_path}"
        )
    return 0


def command_stats(args: argparse.Namespace) -> int:
    settings, store = _with_store(args)
    try:
        rows = store.query_file("stats.cypher", {"repository": settings.repository_id})
    finally:
        store.close()
    if args.json:
        print(_json(rows))
    else:
        _print_rows(rows)
    return 0


def command_reset(args: argparse.Namespace) -> int:
    if not args.yes:
        print("Refusing reset without --yes", file=sys.stderr)
        return 2
    settings, store = _with_store(args)
    try:
        store.reset_repository(settings.repository_id)
    finally:
        store.close()
    print(f"Deleted derived graph projection for {settings.repository_id}")
    return 0


def _add_context_budget_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--depth", type=int)
    parser.add_argument("--max-nodes", type=int)
    parser.add_argument("--max-bytes", type=int)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="graph-engineering")
    parser.add_argument("--repo-root", help="Repository root (auto-discovered by default)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor = subparsers.add_parser("doctor", help="Verify schema definitions and Neo4j connectivity")
    doctor.add_argument("--wait", type=int, default=0, help="Seconds to wait for Neo4j readiness")
    doctor.set_defaults(func=command_doctor)

    schema = subparsers.add_parser("schema", help="Initialize Neo4j constraints/indexes")
    schema.set_defaults(func=command_schema)

    sync = subparsers.add_parser("sync", help="Full idempotent repository projection sync")
    sync.add_argument("--github-event", help="GitHub Actions event JSON path")
    sync.add_argument("--json", action="store_true")
    sync.set_defaults(func=command_sync)

    validate = subparsers.add_parser("validate", help="Run graph architecture invariants")
    validate.add_argument("--json", action="store_true")
    validate.set_defaults(func=command_validate)

    impact = subparsers.add_parser("impact", help="Traverse bounded impact around an entity")
    impact.add_argument("canonical_id")
    impact.add_argument("--depth", type=int, default=3)
    impact.add_argument("--limit", type=int, default=200)
    impact.add_argument("--json", action="store_true")
    impact.set_defaults(func=command_impact)

    ready = subparsers.add_parser("ready", help="List READY/BLOCKED pending tasks")
    ready.add_argument("--spec")
    ready.add_argument("--json", action="store_true")
    ready.set_defaults(func=command_ready)

    conflicts = subparsers.add_parser("conflicts", help="Find pending tasks sharing artifacts")
    conflicts.add_argument("--spec")
    conflicts.add_argument("--json", action="store_true")
    conflicts.set_defaults(func=command_conflicts)

    drift = subparsers.add_parser("drift", help="Show raw architecture/spec-drift evidence")
    drift.add_argument("--json", action="store_true")
    drift.set_defaults(func=command_drift)

    context = subparsers.add_parser("context", help="Build bounded task context package")
    context.add_argument("task_id")
    context.add_argument("--format", choices=("markdown", "json"), default="markdown")
    _add_context_budget_arguments(context)
    context.add_argument("--output")
    context.set_defaults(func=command_context)

    context_batch = subparsers.add_parser(
        "context-batch",
        help="Generate portable context packages for READY or explicitly selected tasks",
    )
    context_batch.add_argument("--spec")
    context_batch.add_argument("--task", action="append", default=[])
    context_batch.add_argument("--output-root")
    _add_context_budget_arguments(context_batch)
    context_batch.add_argument("--json", action="store_true")
    context_batch.set_defaults(func=command_context_batch)

    context_validate = subparsers.add_parser(
        "context-validate",
        help="Validate context package schema/repository/revision freshness",
    )
    context_validate.add_argument("package")
    context_validate.add_argument("--strict", action="store_true")
    context_validate.add_argument("--json", action="store_true")
    context_validate.set_defaults(func=command_context_validate)

    context_adapt = subparsers.add_parser(
        "context-adapt",
        help="Render a portable context package for a supported coding agent",
    )
    context_adapt.add_argument("package")
    context_adapt.add_argument("--agent", required=True, choices=SUPPORTED_AGENTS)
    context_adapt.add_argument("--output")
    context_adapt.set_defaults(func=command_context_adapt)

    waves = subparsers.add_parser("waves", help="Build dependency-safe conflict-free execution waves")
    waves.add_argument("--spec")
    waves.add_argument("--json", action="store_true")
    waves.set_defaults(func=command_waves)

    execution_plan = subparsers.add_parser(
        "execution-plan",
        help="Build a revision-bound Execution Graph manifest",
    )
    execution_plan.add_argument("--spec")
    execution_plan.add_argument("--agent", choices=SUPPORTED_AGENTS, default="codex")
    execution_plan.add_argument("--output")
    execution_plan.add_argument("--json", action="store_true")
    execution_plan.set_defaults(func=command_execution_plan)

    execution_prepare = subparsers.add_parser(
        "execution-prepare",
        help="Prepare one safe execution wave/task set into Git worktrees",
    )
    execution_prepare.add_argument("manifest")
    execution_prepare.add_argument("--wave", type=int)
    execution_prepare.add_argument("--task", action="append", default=[])
    execution_prepare.add_argument("--execution-root")
    execution_prepare.add_argument("--dry-run", action="store_true")
    execution_prepare.add_argument("--json", action="store_true")
    execution_prepare.set_defaults(func=command_execution_prepare)

    execution_status_parser = subparsers.add_parser(
        "execution-status",
        help="Inspect active local Execution Graph leases/worktrees",
    )
    execution_status_parser.add_argument("--execution-root")
    execution_status_parser.add_argument("--json", action="store_true")
    execution_status_parser.set_defaults(func=command_execution_status)

    execution_release = subparsers.add_parser(
        "execution-release",
        help="Release a task lease and optionally remove its generated worktree",
    )
    execution_release.add_argument("task_id")
    execution_release.add_argument("--execution-root")
    execution_release.add_argument("--remove-worktree", action="store_true")
    execution_release.add_argument("--force", action="store_true")
    execution_release.add_argument("--json", action="store_true")
    execution_release.set_defaults(func=command_execution_release)

    stats = subparsers.add_parser("stats", help="Show projected node/relationship counts")
    stats.add_argument("--json", action="store_true")
    stats.set_defaults(func=command_stats)

    reset = subparsers.add_parser("reset", help="Delete this repository's derived projection")
    reset.add_argument("--yes", action="store_true")
    reset.set_defaults(func=command_reset)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except KeyboardInterrupt:
        return 130
    except Exception as error:
        print(f"graph-engineering: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
