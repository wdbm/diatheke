from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from diatheke import DirectoryChooserDialog, _nearest_existing_directory


class _DialogStub:
    def __init__(self) -> None:
        self.errors: list[tuple[str, str, dict[str, object]]] = []

    def _show_error(self, title_key: str, message_key: str, **values) -> None:
        self.errors.append((title_key, message_key, values))


class NearestExistingDirectoryTests(unittest.TestCase):
    def test_none_returns_home_directory(self) -> None:
        self.assertEqual(_nearest_existing_directory(None), Path.home())

    def test_existing_directory_is_returned(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            self.assertEqual(_nearest_existing_directory(directory), directory.resolve())

    def test_existing_file_returns_parent_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            file_path = directory / "example.txt"
            file_path.write_text("example", encoding="utf-8")
            self.assertEqual(_nearest_existing_directory(file_path), directory.resolve())

    def test_nonexistent_nested_path_returns_nearest_existing_parent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            nested_missing_path = directory / "missing" / "child"
            self.assertEqual(_nearest_existing_directory(nested_missing_path), directory.resolve())


class DirectoryFromInputTests(unittest.TestCase):
    def test_existing_directory_is_resolved(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            stub = _DialogStub()
            result = DirectoryChooserDialog._directory_from_input(stub, str(directory))
            self.assertEqual(result, directory.resolve())
            self.assertEqual(stub.errors, [])

    def test_nonexistent_directory_returns_none_and_reports_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            missing_path = Path(temp_dir) / "missing"
            stub = _DialogStub()
            result = DirectoryChooserDialog._directory_from_input(stub, str(missing_path))
            self.assertIsNone(result)
            self.assertEqual(len(stub.errors), 1)
            title_key, message_key, values = stub.errors[0]
            self.assertEqual(title_key, "directory_not_found_title")
            self.assertEqual(message_key, "directory_not_found_message")
            self.assertEqual(values["path"], missing_path.resolve(strict=False))

    def test_file_path_returns_none_and_reports_not_a_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "example.txt"
            file_path.write_text("example", encoding="utf-8")
            stub = _DialogStub()
            result = DirectoryChooserDialog._directory_from_input(stub, str(file_path))
            self.assertIsNone(result)
            self.assertEqual(len(stub.errors), 1)
            title_key, message_key, values = stub.errors[0]
            self.assertEqual(title_key, "not_a_directory_title")
            self.assertEqual(message_key, "not_a_directory_message")
            self.assertEqual(values["path"], file_path.resolve(strict=False))


if __name__ == "__main__":
    unittest.main()
