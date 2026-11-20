"""Markdown section handling in task bodies."""

import unittest

import helpers  # noqa: F401

import mdpm_core as core

BODY_WITH_FENCED_HEADING = (
    "# Z\n"
    "\n"
    "## Notes\n"
    "```md\n"
    "## Work Log\n"
    "- fake\n"
    "```\n"
    "\n"
    "## Work Log\n"
    "- 2026-01-01: real\n"
)


class SectionTests(unittest.TestCase):
    def test_extract_ignores_headings_inside_code_fences(self):
        self.assertEqual(
            core.extract_section(BODY_WITH_FENCED_HEADING, "Work Log"),
            "- 2026-01-01: real",
        )

    def test_worklog_entry_goes_to_the_real_section_not_the_fenced_one(self):
        out = core.append_worklog(BODY_WITH_FENCED_HEADING, "added", when="2026-02-02")
        self.assertEqual(
            out,
            BODY_WITH_FENCED_HEADING + "- 2026-02-02: added\n",
        )

    def test_notes_section_keeps_its_fenced_block_intact(self):
        notes = core.extract_section(BODY_WITH_FENCED_HEADING, "Notes")
        self.assertEqual(notes, "```md\n## Work Log\n- fake\n```")

    def test_tilde_fences_are_respected(self):
        body = "## Notes\n~~~\n## Work Log\n~~~\n\n## Work Log\n- real\n"
        self.assertEqual(core.extract_section(body, "Work Log"), "- real")

    def test_worklog_section_is_created_when_missing(self):
        out = core.append_worklog("# T\n\n## Notes\nhi\n", "first", when="2026-02-02")
        self.assertEqual(core.extract_section(out, "Work Log"), "- 2026-02-02: first")

    def test_acceptance_counts(self):
        body = "## Acceptance Criteria\n- [x] a\n- [ ] b\n- [X] c\n\n## Notes\n- [ ] not counted\n"
        self.assertEqual(core.count_acceptance(body), (2, 3))


if __name__ == "__main__":
    unittest.main()
