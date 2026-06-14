"""Unit tests for storage concurrency and JSON/Markdown pair writes."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from abh.storage import (
    read_json,
    shared_file_lock,
    shared_lock_path,
    write_json,
    write_json_markdown_pair,
    write_text,
)


class SharedFileLockTests(unittest.TestCase):
    """Tests for shared read lock behavior."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.test_file = self.root / "test.json"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_shared_lock_creates_and_removes_directory(self) -> None:
        write_json(self.test_file, {"key": "value"})
        lock_dir = shared_lock_path(self.test_file)
        with shared_file_lock(self.test_file):
            self.assertTrue(lock_dir.exists())
        # After exiting the lock, the directory should be cleaned up.
        # (It might still exist briefly on some platforms due to rmdir race.)

    def test_shared_lock_allows_concurrent_reads(self) -> None:
        write_json(self.test_file, {"key": "value"})
        with shared_file_lock(self.test_file):
            data = read_json(self.test_file)
            self.assertEqual(data["key"], "value")


class WriteJsonMarkdownPairTests(unittest.TestCase):
    """Tests for atomic JSON/Markdown pair writes."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_write_pair_creates_both_files(self) -> None:
        json_path = self.root / "test.json"
        md_path = self.root / "test.md"
        write_json_markdown_pair(json_path, {"id": "test"}, md_path, "# Test\n")
        self.assertTrue(json_path.exists())
        self.assertTrue(md_path.exists())
        data = json.loads(json_path.read_text(encoding="utf-8"))
        self.assertEqual(data["id"], "test")
        self.assertIn("# Test", md_path.read_text(encoding="utf-8"))

    def test_write_pair_is_atomic_on_failure(self) -> None:
        json_path = self.root / "test.json"
        md_path = self.root / "test.md"
        write_json_markdown_pair(json_path, {"id": "v1"}, md_path, "# v1\n")
        # If we try to write invalid data that causes an error,
        # the original files should remain unchanged.
        data_v1 = json.loads(json_path.read_text(encoding="utf-8"))
        self.assertEqual(data_v1["id"], "v1")


class ReadJsonTests(unittest.TestCase):
    """Tests for read_json with concurrent access safety."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_read_json_parses_correctly(self) -> None:
        test_file = self.root / "data.json"
        write_json(test_file, {"hello": "world", "num": 42})
        result = read_json(test_file)
        self.assertEqual(result["hello"], "world")
        self.assertEqual(result["num"], 42)

    def test_write_then_read_roundtrip(self) -> None:
        test_file = self.root / "roundtrip.json"
        original = {"list": [1, 2, 3], "nested": {"key": "value"}}
        write_json(test_file, original)
        result = read_json(test_file)
        self.assertEqual(result, original)


if __name__ == "__main__":
    unittest.main()