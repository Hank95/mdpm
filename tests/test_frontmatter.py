"""Frontmatter parsing, and the guarantee that rewriting a task file never
damages frontmatter the tool did not mean to change."""

import unittest

import helpers  # noqa: F401  (sets up sys.path)
from helpers import ProjectCase

import mdpm_core as core

AWKWARD_STRINGS = [
    'Fix "login" bug: now',
    "it's a trap",
    'both \' and " quotes',
    "back\\slash",
    "trailing hash # not a comment",
    "null",
    "true",
    "[not, a, list]",
    "  padded  ",
    "",
]


class ParseTests(unittest.TestCase):
    def parse(self, block: str) -> dict:
        fm, _ = core.parse_frontmatter(f"---\n{block}\n---\n\n# Body\n")
        return fm

    def test_inline_comment_is_not_part_of_a_scalar(self):
        fm = self.parse("priority: high            # high | medium | low")
        self.assertEqual(fm["priority"], "high")

    def test_inline_comment_after_a_list_is_ignored(self):
        fm = self.parse("depends_on: [PRJ-000] # must be done first")
        self.assertEqual(fm["depends_on"], ["PRJ-000"])

    def test_hash_inside_quotes_is_kept(self):
        fm = self.parse('title: "Fix issue #12"')
        self.assertEqual(fm["title"], "Fix issue #12")

    def test_hash_without_leading_space_is_kept(self):
        fm = self.parse("title: C#-bindings")
        self.assertEqual(fm["title"], "C#-bindings")

    def test_double_quoted_escapes_are_decoded(self):
        fm = self.parse(r'title: "say \"hi\" \\ bye"')
        self.assertEqual(fm["title"], 'say "hi" \\ bye')

    def test_single_quoted_doubled_quote_is_decoded(self):
        fm = self.parse("title: 'it''s fine'")
        self.assertEqual(fm["title"], "it's fine")

    def test_block_list(self):
        fm = self.parse("tags:\n  - a\n  - b")
        self.assertEqual(fm["tags"], ["a", "b"])

    def test_folded_block_scalar(self):
        fm = self.parse("description: >\n  folded text\n  more")
        self.assertEqual(fm["description"], "folded text more")

    def test_literal_block_scalar(self):
        fm = self.parse("description: |\n  line one\n  line two")
        self.assertEqual(fm["description"], "line one\nline two")

    def test_value_containing_a_colon(self):
        fm = self.parse("title: Fix: the thing")
        self.assertEqual(fm["title"], "Fix: the thing")


class RenderRoundTripTests(unittest.TestCase):
    def test_strings_survive_render_then_parse(self):
        for value in AWKWARD_STRINGS:
            with self.subTest(value=value):
                text = core.render_frontmatter({"title": value}) + "\nbody\n"
                fm, _ = core.parse_frontmatter(text)
                self.assertEqual(fm["title"], value)

    def test_lists_of_awkward_strings_survive(self):
        tags = ["a,b", 'q"uote', "plain", "x: y"]
        text = core.render_frontmatter({"tags": tags}) + "\nbody\n"
        fm, _ = core.parse_frontmatter(text)
        self.assertEqual(fm["tags"], tags)

    def test_multiline_string_survives(self):
        text = core.render_frontmatter({"description": "one\ntwo"}) + "\nbody\n"
        fm, _ = core.parse_frontmatter(text)
        self.assertEqual(fm["description"], "one\ntwo")


class RewritePreservationTests(ProjectCase):
    """Writing a task back must leave untouched frontmatter lines byte-identical."""

    HAND_WRITTEN = (
        "---\n"
        "id: PRJ-007\n"
        "title: Hand written\n"
        "priority: high            # high | medium | low\n"
        "# a full-line comment\n"
        "tags:\n"
        "  - alpha\n"
        "  - beta\n"
        "description: >\n"
        "  folded text\n"
        "  more\n"
        "custom_field: keep me\n"
        "---\n"
        "\n"
        "# Hand written\n"
        "\n"
        "## Work Log\n"
        "- 2026-01-01: Task created.\n"
    )

    def rewrite(self, **changes) -> str:
        path = self.write_task("backlog", "PRJ-007-hand-written.md", self.HAND_WRITTEN)
        task = core.load_task(path, "backlog")
        fm = dict(task["frontmatter"])
        fm.update(changes)
        core.write_task_file(path, fm, task["body"])
        return path.read_text(encoding="utf-8")

    def test_unchanged_frontmatter_is_byte_identical(self):
        self.assertEqual(self.rewrite(), self.HAND_WRITTEN)

    def test_changing_one_field_leaves_the_others_alone(self):
        out = self.rewrite(title="Renamed")
        self.assertEqual(out, self.HAND_WRITTEN.replace("title: Hand written", "title: Renamed"))

    def test_new_field_is_appended_inside_the_frontmatter(self):
        out = self.rewrite(updated="2026-02-02")
        expected = self.HAND_WRITTEN.replace(
            "custom_field: keep me\n", "custom_field: keep me\nupdated: 2026-02-02\n"
        )
        self.assertEqual(out, expected)

    def test_changed_multiline_field_replaces_all_of_its_lines(self):
        out = self.rewrite(tags=["gamma"])
        self.assertIn("tags: [gamma]\n", out)
        self.assertNotIn("- alpha", out)
        self.assertIn("description: >\n  folded text\n  more\n", out)

    def test_title_with_quotes_is_stable_across_repeated_cli_writes(self):
        title = 'Fix "login" bug: now'
        self.cli("new", title)
        self.cli("log", "PRJ-001", "one")
        self.cli("log", "PRJ-001", "two")
        fm, _ = core.parse_frontmatter(self.only_task("backlog").read_text(encoding="utf-8"))
        self.assertEqual(fm["title"], title)


if __name__ == "__main__":
    unittest.main()
