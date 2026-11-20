"""Shared test helpers: import paths and a throwaway MDPM project."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MDPM = REPO / "bin" / "mdpm"

sys.path.insert(0, str(REPO / "lib"))
sys.path.insert(0, str(REPO / "board"))


class ProjectCase(unittest.TestCase):
    """A test case with an empty MDPM project in a temp directory."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name).resolve()
        for status in ("inbox", "backlog", "active", "done"):
            (self.root / "tasks" / status).mkdir(parents=True)

    def run_cli(self, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(MDPM), *args],
            cwd=str(cwd or self.root),
            capture_output=True,
            text=True,
        )

    def cli(self, *args: str) -> str:
        """Run the CLI, assert success, return stdout."""
        result = self.run_cli(*args)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def cli_json(self, *args: str) -> dict:
        return json.loads(self.cli("--json", *args))

    def write_task(self, status: str, filename: str, text: str) -> Path:
        path = self.root / "tasks" / status / filename
        path.write_text(text, encoding="utf-8")
        return path

    def only_task(self, status: str) -> Path:
        files = sorted((self.root / "tasks" / status).glob("*.md"))
        self.assertEqual(len(files), 1, files)
        return files[0]
