from __future__ import annotations

import unittest

from engineering_graph.runner_entry import (
    LOCAL_COMMANDS,
    VALIDATION_COMMANDS,
    _command_token,
    _runner_parser,
)


class AgentValidatorCliTests(unittest.TestCase):
    def test_validation_run_has_no_command_override(self) -> None:
        parser = _runner_parser()
        args = parser.parse_args(["validation-run", "SPEC-015-AGENT-VALIDATOR:T040", "--json"])
        self.assertEqual(args.command, "validation-run")
        self.assertEqual(args.task_id, "SPEC-015-AGENT-VALIDATOR:T040")
        self.assertFalse(hasattr(args, "validation_command"))

    def test_validation_status_filters_are_registered(self) -> None:
        parser = _runner_parser()
        args = parser.parse_args(
            ["validation-status", "--task", "SPEC-015-AGENT-VALIDATOR:T040", "--validation", "v1", "--json"]
        )
        self.assertEqual(args.command, "validation-status")
        self.assertEqual(args.task, "SPEC-015-AGENT-VALIDATOR:T040")
        self.assertEqual(args.validation, "v1")

    def test_entrypoint_routes_validation_commands_locally(self) -> None:
        self.assertTrue(VALIDATION_COMMANDS <= LOCAL_COMMANDS)
        for command in VALIDATION_COMMANDS:
            self.assertEqual(_command_token([command]), command)
            self.assertEqual(_command_token(["--repo-root", "/tmp/repo", command]), command)


if __name__ == "__main__":
    unittest.main()
