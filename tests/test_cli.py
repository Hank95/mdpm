"""End-to-end CLI behaviour, run as a subprocess against a temp project."""

import json
import tempfile
import unittest
from pathlib import Path

from helpers import REPO, ProjectCase

import mdpm_core as core


class LifecycleTests(ProjectCase):
    def test_new_creates_a_backlog_file_named_from_id_and_title(self):
        out = self.cli_json("new", "Add user login", "--priority", "high", "--tags", "auth,bug")
        self.assertEqual(out["task"]["id"], "PRJ-001")
        path = self.root / "tasks" / "backlog" / "PRJ-001-add-user-login.md"
        fm, _ = core.parse_frontmatter(path.read_text(encoding="utf-8"))
        self.assertEqual((fm["priority"], fm["tags"], fm["status"]), ("high", ["auth", "bug"], "backlog"))

    def test_ids_increment_and_are_not_reused_after_archiving(self):
        self.cli("new", "One")
        self.cli("done", "PRJ-001", "--no-changelog")
        self.cli("archive", "--all")
        self.assertEqual(self.cli_json("new", "Two")["task"]["id"], "PRJ-002")

    def test_start_moves_the_file_and_logs_it(self):
        self.cli("new", "One")
        self.cli("start", "PRJ-001")
        text = self.only_task("active").read_text(encoding="utf-8")
        self.assertIn("status: active", text)
        self.assertIn("Started work.", core.extract_section(text, "Work Log"))

    def test_start_refuses_unmet_dependencies(self):
        self.cli("new", "First")
        self.cli("new", "Second", "--depends", "PRJ-001")
        result = self.run_cli("start", "PRJ-002")
        self.assertEqual(result.returncode, 4)
        self.assertIn("PRJ-001", result.stderr)

    def test_done_reports_newly_unblocked_dependents(self):
        self.cli("new", "First")
        self.cli("new", "Second", "--depends", "PRJ-001")
        out = self.cli_json("done", "PRJ-001", "-m", "Shipped")
        self.assertEqual([u["id"] for u in out["unblocked"]], ["PRJ-002"])

    def test_done_writes_a_changelog_entry(self):
        self.cli("new", "First")
        self.cli("done", "PRJ-001", "-m", "Shipped it")
        changelog = (self.root / "docs" / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertIn("- [PRJ-001] First — Shipped it.", changelog)

    def test_done_warns_about_unchecked_acceptance_criteria(self):
        self.cli("new", "First")
        path = self.only_task("backlog")
        path.write_text(
            path.read_text(encoding="utf-8").replace(
                "## Acceptance Criteria\n", "## Acceptance Criteria\n- [ ] not yet\n"
            ),
            encoding="utf-8",
        )
        out = self.cli_json("done", "PRJ-001", "--no-changelog")
        self.assertEqual(out["warnings"], ["1 unchecked acceptance criteria remaining"])

    def test_block_and_unblock_keep_the_task_in_place(self):
        self.cli("new", "First")
        self.assertEqual(self.cli_json("block", "PRJ-001", "waiting", "on", "review")["task"]["status"], "blocked")
        self.assertEqual(self.cli_json("unblock", "PRJ-001")["task"]["status"], "backlog")
        self.only_task("backlog")

    def test_edit_title_renames_the_file(self):
        self.cli("new", "Old name")
        self.cli("edit", "PRJ-001", "--title", "New name")
        self.assertEqual(self.only_task("backlog").name, "PRJ-001-new-name.md")

    def test_edit_rejects_a_dependency_cycle(self):
        self.cli("new", "First")
        self.cli("new", "Second", "--depends", "PRJ-001")
        result = self.run_cli("edit", "PRJ-001", "--depends", "PRJ-002")
        self.assertEqual(result.returncode, 3)
        self.assertIn("circular dependency", result.stderr)

    def test_ambiguous_ref_exits_2_with_candidates(self):
        self.cli("new", "Gallery page")
        self.cli("new", "Gallery analytics")
        result = self.run_cli("--json", "show", "gallery")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(len(json.loads(result.stdout)["candidates"]), 2)

    def test_next_prefers_high_priority_and_skips_waiting_tasks(self):
        self.cli("new", "Low one", "--priority", "low")
        self.cli("new", "High but waiting", "--priority", "high", "--depends", "PRJ-001")
        self.cli("new", "Medium one")
        self.assertEqual(self.cli_json("next")["recommendation"]["id"], "PRJ-003")


class ReadingHandWrittenFilesTests(ProjectCase):
    TASK = (
        "---\n"
        "id: PRJ-002\n"
        "title: Commented\n"
        "priority: high            # high | medium | low\n"
        "status: backlog\n"
        "due: 2020-01-01   # soon\n"
        "---\n\n"
        "# Commented\n\n"
        "## Objective\nneedle-in-objective\n\n"
        "## Acceptance Criteria\n- [ ] needle-in-criteria\n\n"
        "## Work Log\n- 2026-01-01: needle-in-old-log\n- 2026-01-02: latest\n"
    )

    def setUp(self):
        super().setUp()
        self.write_task("backlog", "PRJ-002-commented.md", self.TASK)

    def test_priority_filter_matches_a_commented_field(self):
        self.assertEqual(self.cli_json("list", "--priority", "high")["count"], 1)

    def test_overdue_is_detected_through_an_inline_comment(self):
        self.assertEqual(self.cli_json("list", "--overdue")["count"], 1)

    def test_search_finds_text_in_acceptance_criteria(self):
        self.assertEqual(self.cli_json("search", "needle-in-criteria")["count"], 1)

    def test_search_finds_text_in_older_work_log_entries(self):
        self.assertEqual(self.cli_json("search", "needle-in-old-log")["count"], 1)


class GlobalFlagTests(ProjectCase):
    def test_json_flag_works_after_the_subcommand(self):
        self.assertEqual(json.loads(self.cli("list", "--json"))["action"], "list")

    def test_json_flag_works_before_the_subcommand(self):
        self.assertEqual(json.loads(self.cli("--json", "list"))["action"], "list")

    def test_root_flag_works_after_the_subcommand(self):
        self.cli("new", "One")
        with tempfile.TemporaryDirectory() as elsewhere:
            result = self.run_cli("list", "--json", "--root", str(self.root), cwd=Path(elsewhere))
        self.assertEqual(json.loads(result.stdout)["count"], 1)


class SessionContextTests(ProjectCase):
    """`mdpm session-context` is what the plugin's SessionStart hook runs."""

    def test_prints_nothing_outside_an_mdpm_project(self):
        with tempfile.TemporaryDirectory() as elsewhere:
            result = self.run_cli("session-context", cwd=Path(elsewhere))
        self.assertEqual((result.returncode, result.stdout), (0, ""))

    def test_a_bare_tasks_directory_is_not_enough(self):
        # Plenty of unrelated repos have a tasks/ folder; only .mdpm/ opts in.
        result = self.run_cli("session-context")
        self.assertEqual((result.returncode, result.stdout), (0, ""))

    def test_prints_the_cli_rules_with_a_runnable_path_inside_a_project(self):
        (self.root / ".mdpm").mkdir()
        (self.root / ".mdpm" / "config.json").write_text("{}", encoding="utf-8")
        sub = self.root / "src" / "deep"
        sub.mkdir(parents=True)
        out = self.run_cli("session-context", cwd=sub).stdout
        self.assertIn("Use the CLI", out)
        self.assertIn(str(REPO / "bin" / "mdpm"), out)
        self.assertNotIn("${CLAUDE_PLUGIN_ROOT}", out)


if __name__ == "__main__":
    unittest.main()
