from __future__ import annotations

import unittest

from engineering_graph.cli import build_parser


class ExecutionCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.parser = build_parser()

    def test_execution_plan_parser(self) -> None:
        args = self.parser.parse_args(
            [
                "execution-plan",
                "--spec",
                "SPEC-011-EXECUTION-GRAPH",
                "--agent",
                "claude",
                "--output",
                "/tmp/manifest.json",
                "--json",
            ]
        )
        self.assertEqual(args.command, "execution-plan")
        self.assertEqual(args.spec, "SPEC-011-EXECUTION-GRAPH")
        self.assertEqual(args.agent, "claude")
        self.assertEqual(args.output, "/tmp/manifest.json")
        self.assertTrue(args.json)

    def test_execution_prepare_wave_parser(self) -> None:
        args = self.parser.parse_args(
            [
                "execution-prepare",
                "/tmp/manifest.json",
                "--wave",
                "2",
                "--execution-root",
                "/tmp/execution",
                "--dry-run",
                "--json",
            ]
        )
        self.assertEqual(args.command, "execution-prepare")
        self.assertEqual(args.manifest, "/tmp/manifest.json")
        self.assertEqual(args.wave, 2)
        self.assertEqual(args.task, [])
        self.assertTrue(args.dry_run)

    def test_execution_prepare_explicit_tasks_parser(self) -> None:
        args = self.parser.parse_args(
            [
                "execution-prepare",
                "/tmp/manifest.json",
                "--task",
                "SPEC-011:T001",
                "--task",
                "SPEC-011:T002",
            ]
        )
        self.assertIsNone(args.wave)
        self.assertEqual(args.task, ["SPEC-011:T001", "SPEC-011:T002"])

    def test_execution_status_parser(self) -> None:
        args = self.parser.parse_args(["execution-status", "--json"])
        self.assertEqual(args.command, "execution-status")
        self.assertTrue(args.json)

    def test_execution_release_parser(self) -> None:
        args = self.parser.parse_args(
            [
                "execution-release",
                "SPEC-011:T001",
                "--remove-worktree",
                "--force",
                "--json",
            ]
        )
        self.assertEqual(args.command, "execution-release")
        self.assertEqual(args.task_id, "SPEC-011:T001")
        self.assertTrue(args.remove_worktree)
        self.assertTrue(args.force)
        self.assertTrue(args.json)

    def test_execution_plan_rejects_unknown_agent(self) -> None:
        with self.assertRaises(SystemExit):
            self.parser.parse_args(
                [
                    "execution-plan",
                    "--agent",
                    "unknown",
                ]
            )


if __name__ == "__main__":
    unittest.main()
