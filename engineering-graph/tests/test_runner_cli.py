from __future__ import annotations

import unittest

from engineering_graph.runner_entry import RUNNER_COMMANDS, _command_token, _runner_parser


class AgentRunnerCliTests(unittest.TestCase):
    def test_runner_start_consumes_literal_argv_remainder(self) -> None:
        parser = _runner_parser()
        args = parser.parse_args(
            [
                "runner-start",
                "SPEC-013-AGENT-RUNNER:T057",
                "--stdin-handoff",
                "--json",
                "--command",
                "python",
                "-c",
                "print('fixture')",
                "--agent-owned-flag",
            ]
        )
        self.assertEqual(args.command[0], "python")
        self.assertEqual(args.command[1], "-c")
        self.assertEqual(args.command[-1], "--agent-owned-flag")
        self.assertTrue(args.stdin_handoff)
        self.assertTrue(args.json)

    def test_status_stop_and_logs_are_registered(self) -> None:
        parser = _runner_parser()
        status = parser.parse_args(["runner-status", "--task", "SPEC-013:T001", "--json"])
        stop = parser.parse_args(["runner-stop", "SPEC-013:T001", "--force", "--timeout", "1"])
        logs = parser.parse_args(["runner-logs", "SPEC-013:T001", "--stream", "both"])
        self.assertEqual(status.command, "runner-status")
        self.assertEqual(stop.command, "runner-stop")
        self.assertTrue(stop.force)
        self.assertEqual(logs.command, "runner-logs")
        self.assertEqual(logs.stream, "both")

    def test_entrypoint_routes_only_runner_commands(self) -> None:
        for command in RUNNER_COMMANDS:
            self.assertEqual(_command_token([command]), command)
            self.assertEqual(_command_token(["--repo-root", "/tmp/repo", command]), command)
        self.assertEqual(_command_token(["execution-status"]), "execution-status")
        self.assertEqual(_command_token(["--repo-root=/tmp/repo", "graphrag-status"]), "graphrag-status")


if __name__ == "__main__":
    unittest.main()
