from __future__ import annotations

import unittest

from kvconfig import parse_lines


class ParseLinesTests(unittest.TestCase):
    def test_parses_and_normalizes_keys(self) -> None:
        self.assertEqual(
            parse_lines(["Deploy-Env = staging", "worker count=4"]),
            {"deploy_env": "staging", "worker_count": "4"},
        )

    def test_ignores_comments_and_blanks(self) -> None:
        self.assertEqual(parse_lines(["", " # note", "PORT=8080"]), {"port": "8080"})

    def test_rejects_malformed_line(self) -> None:
        with self.assertRaisesRegex(ValueError, "line 2"):
            parse_lines(["OK=yes", "missing delimiter"])


if __name__ == "__main__":
    unittest.main()
