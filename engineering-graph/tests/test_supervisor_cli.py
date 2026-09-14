from __future__ import annotations

import unittest

from engineering_graph.runner_entry import (
    LOCAL_COMMANDS,
    RUNNER_COMMANDS,
    SUPERVISOR_COMMANDS,
    _command_token,
    _runner_parser,
)


class AgentSupervisorCliTests(unittest.TestCase):
    def test_supervisor_start_consumes_literal_argv_remainder(self) -> None:
        parser = _runner_parser()
        args = parser.parse_args(
            [
                "supervisor-start",
                "/tmp/execution.json",
                "--wave",
                "2",
                "--max-parallel",
                "3",
                "--max-attempts",
                "2",
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
        self.assertEqual(args.wave, 2)
        self.assertEqual(args.max_parallel, 3)
        self.assertEqual(args.max_attempts, 2)
        self.assertTrue(args.stdin_handoff)
        self.assertTrue(args.json)

    def test_tick_status_and_stop_are_registered(self) -> None:
        parser = _runner_parser()
        tick = parser.parse_args(["supervisor-tick", "job-1", "--json"])
        status = parser.parse_args(["supervisor-status", "--job", "job-1", "--json"])
        stop = parser.parse_args(["supervisor-stop", "job-1", "--force", "--timeout", "1"])
        self.assertEqual(tick.command, "supervisor-tick")
        self.assertEqual(status.command, "supervisor-status")
        self.assertEqual(status.job, "job-1")
        self.assertEqual(stop.command, "supervisor-stop")
        self.assertTrue(stop.force)

    def test_entrypoint_routes_runner_and_supervisor_commands(self) -> None:
        self.assertTrue(RUNNER_COMMANDS <= LOCAL_COMMANDS)
        self.assertTrue(SUPERVISOR_COMMANDS <= LOCAL_COMMANDS)
        for command in LOCAL_COMMANDS:
            self.assertEqual(_command_token([command]), command)
            self.assertEqual(_command_token(["--repo-root", "/tmp/repo", command]), command)
        self.assertEqual(_command_token(["execution-status"]), "execution-status")


if __name__ == "__main__":
    unittest.main()
