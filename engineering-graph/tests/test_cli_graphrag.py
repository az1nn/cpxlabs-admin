from __future__ import annotations

import unittest

from engineering_graph.cli import build_parser


class GraphRagCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.parser = build_parser()

    def test_build_parser(self) -> None:
        args = self.parser.parse_args(
            [
                "graphrag-build",
                "--provider",
                "hashing",
                "--dimensions",
                "64",
                "--output",
                "/tmp/index.json",
                "--json",
            ]
        )
        self.assertEqual(args.command, "graphrag-build")
        self.assertEqual(args.provider, "hashing")
        self.assertEqual(args.dimensions, 64)
        self.assertEqual(args.output, "/tmp/index.json")
        self.assertTrue(args.json)

    def test_query_parser(self) -> None:
        args = self.parser.parse_args(
            [
                "graphrag-query",
                "worktree lease architecture",
                "--index",
                "/tmp/index.json",
                "--top-k",
                "5",
                "--min-score",
                "0.15",
                "--depth",
                "3",
                "--max-nodes",
                "40",
                "--mode",
                "architecture",
                "--allow-stale",
                "--json",
            ]
        )
        self.assertEqual(args.query, "worktree lease architecture")
        self.assertEqual(args.top_k, 5)
        self.assertAlmostEqual(args.min_score, 0.15)
        self.assertEqual(args.depth, 3)
        self.assertEqual(args.max_nodes, 40)
        self.assertEqual(args.mode, "architecture")
        self.assertTrue(args.allow_stale)

    def test_validate_parser(self) -> None:
        args = self.parser.parse_args(
            ["graphrag-validate", "/tmp/index.json", "--strict", "--json"]
        )
        self.assertEqual(args.index, "/tmp/index.json")
        self.assertTrue(args.strict)

    def test_status_parser(self) -> None:
        args = self.parser.parse_args(
            ["graphrag-status", "--index", "/tmp/index.json", "--json"]
        )
        self.assertEqual(args.index, "/tmp/index.json")
        self.assertTrue(args.json)

    def test_rejects_unknown_provider(self) -> None:
        with self.assertRaises(SystemExit):
            self.parser.parse_args(["graphrag-build", "--provider", "unknown"])


if __name__ == "__main__":
    unittest.main()
