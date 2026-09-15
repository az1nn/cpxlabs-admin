from __future__ import annotations

import argparse
import unittest

from engineering_graph.publisher_cli import register_publisher_subcommands


def publisher_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="graph-engineering")
    subparsers = parser.add_subparsers(dest="command", required=True)
    register_publisher_subcommands(subparsers)
    return parser


class GitPublisherCliTests(unittest.TestCase):
    def test_publication_run_arguments(self) -> None:
        parser = publisher_parser()
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
        parser = publisher_parser()
        resume = parser.parse_args(["publication-resume", "pub-1", "--json"])
        status = parser.parse_args(["publication-status", "--publication", "pub-1", "--json"])
        self.assertEqual(resume.publication_id, "pub-1")
        self.assertEqual(status.publication, "pub-1")


if __name__ == "__main__":
    unittest.main()
