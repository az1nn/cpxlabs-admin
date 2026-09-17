from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch

from engineering_graph import lifecycle_cli, runner_entry
from engineering_graph.lifecycle import LifecycleBlocker

TASK = "SPEC-018-LIFECYCLE-COORDINATOR:T008"
HEAD = "a" * 40


class LifecycleCliTests(unittest.TestCase):
    def test_runner_parser_exposes_v10_arguments(self) -> None:
        parser = runner_entry._runner_parser()
        args = parser.parse_args(
            [
                "lifecycle-status",
                "--task",
                TASK,
                "--base",
                "develop",
                "--execution-root",
                "/tmp/execution",
                "--human-gates",
                "/tmp/gates.json",
                "--no-pr-inspect",
                "--json",
            ]
        )
        self.assertEqual(args.command, "lifecycle-status")
        self.assertEqual(args.task, TASK)
        self.assertEqual(args.base, "develop")
        self.assertEqual(args.execution_root, "/tmp/execution")
        self.assertEqual(args.human_gates, "/tmp/gates.json")
        self.assertTrue(args.no_pr_inspect)
        self.assertTrue(args.json)

    @patch("engineering_graph.lifecycle_cli.assess_lifecycle")
    @patch("engineering_graph.lifecycle_cli.collect_lifecycle_evidence")
    @patch("engineering_graph.lifecycle_cli._settings")
    def test_json_output_and_read_options(
        self,
        settings_mock,
        collect_mock,
        assess_mock,
    ) -> None:
        settings = MagicMock()
        settings_mock.return_value = settings
        evidence = MagicMock(base_branch="master", publication=None)
        collect_mock.return_value = evidence
        assessment = MagicMock(
            phase="validated",
            next_action="run_publication",
            task_id=TASK,
            repository="example/repo",
            head_sha=HEAD,
            blockers=(),
            evidence=evidence,
        )
        assessment.to_dict.return_value = {
            "phase": "validated",
            "nextAction": "run_publication",
        }
        assess_mock.return_value = assessment

        args = MagicMock(
            repo_root=None,
            execution_root="/tmp/execution",
            human_gates="/tmp/gates.json",
            no_pr_inspect=True,
            base="master",
            task=TASK,
            json=True,
        )
        output = StringIO()
        with redirect_stdout(output):
            code = lifecycle_cli.command_lifecycle_status(args)

        self.assertEqual(code, 0)
        self.assertIn('"nextAction": "run_publication"', output.getvalue())
        collect_mock.assert_called_once_with(
            settings,
            TASK,
            human_gates_path=Path("/tmp/gates.json").resolve(),
            root_override=Path("/tmp/execution").resolve(),
            inspect_pr=False,
            base_branch="master",
        )

    @patch("engineering_graph.lifecycle_cli.assess_lifecycle")
    @patch("engineering_graph.lifecycle_cli.collect_lifecycle_evidence")
    @patch("engineering_graph.lifecycle_cli._settings")
    def test_human_output_and_blocked_exit_code(
        self,
        settings_mock,
        collect_mock,
        assess_mock,
    ) -> None:
        settings_mock.return_value = MagicMock()
        evidence = MagicMock(base_branch="master", publication=None)
        collect_mock.return_value = evidence
        blocker = LifecycleBlocker("identity_conflict", "branch conflict")
        assessment = MagicMock(
            phase="blocked",
            next_action="repair_evidence",
            task_id=TASK,
            repository="example/repo",
            head_sha=HEAD,
            blockers=(blocker,),
            evidence=evidence,
        )
        assessment.to_dict.return_value = {
            "continuation": {"unresolvedHumanAsyncGates": []}
        }
        assess_mock.return_value = assessment
        args = MagicMock(
            repo_root=None,
            execution_root=None,
            human_gates=None,
            no_pr_inspect=False,
            base="master",
            task=TASK,
            json=False,
        )

        output = StringIO()
        with redirect_stdout(output):
            code = lifecycle_cli.command_lifecycle_status(args)

        self.assertEqual(code, 1)
        rendered = output.getvalue()
        self.assertIn("phase=blocked", rendered)
        self.assertIn("next=repair_evidence", rendered)
        self.assertIn("blocker[identity_conflict]: branch conflict", rendered)

    @patch("engineering_graph.lifecycle_cli.command_lifecycle_status")
    def test_runner_entry_routes_lifecycle_status_as_local_command(self, command) -> None:
        command.return_value = 0
        code = runner_entry.main(["lifecycle-status", "--task", TASK])
        self.assertEqual(code, 0)
        command.assert_called_once()


if __name__ == "__main__":
    unittest.main()
