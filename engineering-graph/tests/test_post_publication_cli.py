from __future__ import annotations

import unittest

from engineering_graph.runner_entry import POST_PUBLICATION_COMMANDS, _command_token, _runner_parser


class PostPublicationCliTests(unittest.TestCase):
    def test_status_and_finalize_are_registered(self) -> None:
        parser = _runner_parser()
        status = parser.parse_args(
            ["post-publication-status", "--publication", "pub-1", "--json"]
        )
        finalize = parser.parse_args(
            [
                "post-publication-finalize",
                "--publication",
                "pub-1",
                "--release-lease",
                "--remove-worktree",
                "--json",
            ]
        )
        self.assertEqual(status.command, "post-publication-status")
        self.assertEqual(status.publication, "pub-1")
        self.assertTrue(status.json)
        self.assertEqual(finalize.command, "post-publication-finalize")
        self.assertTrue(finalize.release_lease)
        self.assertTrue(finalize.remove_worktree)

    def test_entrypoint_routes_v9_commands(self) -> None:
        for command in POST_PUBLICATION_COMMANDS:
            self.assertEqual(_command_token([command]), command)
            self.assertEqual(_command_token(["--repo-root", "/tmp/repo", command]), command)


if __name__ == "__main__":
    unittest.main()
