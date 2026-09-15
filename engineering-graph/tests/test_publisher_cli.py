from __future__ import annotations

import unittest

from engineering_graph.runner_entry import (
    LOCAL_COMMANDS,
    PUBLISHER_COMMANDS,
    _command_token,
    _runner_parser,
)


class GitPublisherCliTests(unittest.TestCase):
    def test_publication_run_arguments(self) -> None:
        parser = _runner_parser()
        args = parser.parse_args(
            [
                "publication-run",
                "SPEC-016-GIT-PUBLISHER:T010",
                "--validation",
                "val-1",
                "--commit-message",
                "feat: task",
                "--pr-title",
                "feat: task",
                "--pr-body",
                "validated",
                "--base",
                "master",
                "--json",
            ]
        )
        self.assertEqual(args.command, "publication-run")
        self.assertEqual(args.validation, "val-1")
        self.assertEqual(args.commit_message, "feat: task")
        self.assertEqual(args.base, "master")
        self.assertTrue(args.json)

    def test_resume_and_status_are_registered(self) -> None:
        parser = _runner_parser()
        resume = parser.parse_args(["publication-resume", "pub-1", "--json"])
        status = parser.parse_args(["publication-status", "--publication", "pub-1", "--json"])
        self.assertEqual(resume.publication_id, "pub-1")
        self.assertEqual(status.publication, "pub-1")

    def test_entrypoint_routes_publisher_commands(self) -> None:
        self.assertTrue(PUBLISHER_COMMANDS <= LOCAL_COMMANDS)
        for command in PUBLISHER_COMMANDS:
            self.assertEqual(_command_token([command]), command)
            self.assertEqual(_command_token(["--repo-root", "/tmp/repo", command]), command)


if __name__ == "__main__":
    unittest.main()
