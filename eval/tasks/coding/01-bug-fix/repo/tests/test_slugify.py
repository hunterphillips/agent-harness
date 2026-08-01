from __future__ import annotations

import unittest

from slugify import slugify


class SlugifyTests(unittest.TestCase):
    def test_words_and_case(self) -> None:
        self.assertEqual(slugify("Quarterly Report"), "quarterly-report")

    def test_repeated_whitespace_and_hyphens(self) -> None:
        self.assertEqual(slugify("  north --  star  "), "north-star")

    def test_unicode_letters_and_digits(self) -> None:
        self.assertEqual(slugify("Café 42"), "café-42")

    def test_empty_and_only_separators(self) -> None:
        self.assertEqual(slugify(""), "")
        self.assertEqual(slugify(" -- "), "")

    def test_collapses_mixed_separators(self) -> None:
        self.assertEqual(slugify("Release__Notes / 2026"), "release-notes-2026")


if __name__ == "__main__":
    unittest.main()
