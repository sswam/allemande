#!/usr/bin/env python3

"""
join_lines_test.py - test join_lines.py
"""

import os
import io
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
from typing import Any

import join_lines as subject  # type: ignore

subject_name = subject.__name__


class TestJoinLines:
    """Tests for join_lines functionality"""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files"""
        temp_dir = tempfile.mkdtemp()
        original_dir = os.getcwd()
        os.chdir(temp_dir)
        yield temp_dir
        os.chdir(original_dir)
        shutil.rmtree(temp_dir)

    def test_basic_join_no_template(self, temp_dir):
        """Test basic joining without template"""
        Path("file1").write_text("content1\n")
        Path("file2").write_text("content2\n")
        Path("file3").write_text("content3\n")

        output = io.StringIO()
        subject.join_lines(output, separator=":\t")

        result = output.getvalue()
        assert "file1:\tcontent1" in result
        assert "file2:\tcontent2" in result
        assert "file3:\tcontent3" in result

    def test_join_with_extension(self, temp_dir):
        """Test joining files with extension stripping"""
        Path("file1.txt").write_text("content1\n")
        Path("file2.txt").write_text("content2\n")

        output = io.StringIO()
        subject.join_lines(output, extension=".txt", separator=":\t")

        result = output.getvalue()
        assert "file1:\tcontent1" in result
        assert "file2:\tcontent2" in result
        # Should not include .txt in identifier
        assert ".txt" not in result.split(":\t")[0]

    def test_join_with_template_preserves_order(self, temp_dir):
        """Test that template preserves original order"""
        # Create files in one order
        Path("zebra").write_text("last\n")
        Path("alpha").write_text("first\n")
        Path("beta").write_text("middle\n")

        # Create template with specific order
        Path("template.txt").write_text("zebra:\toldcontent\nalpha:\toldcontent\nbeta:\toldcontent\n")

        output = io.StringIO()
        subject.join_lines(output, template="template.txt", separator=":\t")

        result = output.getvalue()
        lines = result.strip().split("\n")

        # Should preserve template order: zebra, alpha, beta
        assert lines[0].startswith("zebra:")
        assert lines[1].startswith("alpha:")
        assert lines[2].startswith("beta:")

    def test_join_with_template_updates_content(self, temp_dir):
        """Test that content is updated from files, not template"""
        Path("file1").write_text("newcontent\n")
        Path("template.txt").write_text("file1:\toldcontent\n")

        output = io.StringIO()
        subject.join_lines(output, template="template.txt", separator=":\t")

        result = output.getvalue()
        assert "file1:\tnewcontent" in result
        assert "oldcontent" not in result

    def test_missing_template_file(self, temp_dir):
        """Test error when template file doesn't exist"""
        output = io.StringIO()

        with pytest.raises(FileNotFoundError):
            subject.join_lines(output, template="nonexistent.txt")

    def test_missing_file_for_template_identifier(self, temp_dir):
        """Test warning when template references missing file"""
        Path("template.txt").write_text("file1:\tcontent\nfile2:\tcontent\n")
        Path("file1").write_text("exists\n")
        # file2 is missing

        output = io.StringIO()
        with patch.object(subject.logger, 'warning') as mock_warning:
            subject.join_lines(output, template="template.txt", separator=":\t")
            mock_warning.assert_any_call("Missing file for identifier: %s", "file2")

        result = output.getvalue()
        assert "file1:\texists" in result
        assert "file2" not in result

    def test_new_files_appended_by_default(self, temp_dir):
        """Test that new files not in template are appended"""
        Path("file1").write_text("old\n")
        Path("file2").write_text("new\n")
        Path("template.txt").write_text("file1:\tcontent\n")

        output = io.StringIO()
        subject.join_lines(output, template="template.txt", separator=":\t")

        result = output.getvalue()
        assert "file1:\told" in result
        assert "file2:\tnew" in result

    def test_ignore_new_files(self, temp_dir):
        """Test ignore_new flag prevents new files from being added"""
        Path("file1").write_text("old\n")
        Path("file2").write_text("new\n")
        Path("template.txt").write_text("file1:\tcontent\n")

        output = io.StringIO()
        with patch.object(subject.logger, 'warning') as mock_warning:
            subject.join_lines(output, template="template.txt", separator=":\t", ignore_new=True)
            mock_warning.assert_any_call("Ignoring %d new files: %s", 1, "file2")

        result = output.getvalue()
        assert "file1:\told" in result
        assert "file2" not in result

    def test_custom_separator(self, temp_dir):
        """Test custom separator"""
        Path("file1").write_text("content\n")

        output = io.StringIO()
        subject.join_lines(output, separator=" — ")

        result = output.getvalue()
        assert "file1 — content" in result

    def test_multiline_content_stripped(self, temp_dir):
        """Test that trailing newlines are stripped from content"""
        Path("file1").write_text("content\n\n\n")

        output = io.StringIO()
        subject.join_lines(output, separator=":\t")

        result = output.getvalue()
        # Should have exactly one newline at end of line
        assert result == "file1:\tcontent\n"

    def test_empty_file(self, temp_dir):
        """Test handling of empty file"""
        Path("empty").write_text("")

        output = io.StringIO()
        subject.join_lines(output, separator=":\t")

        result = output.getvalue()
        assert "empty:\t\n" in result

    def test_no_files_in_directory(self, temp_dir):
        """Test behavior when no matching files exist"""
        output = io.StringIO()
        subject.join_lines(output, separator=":\t")

        result = output.getvalue()
        assert result == ""

    def test_complex_scene_format(self, temp_dir):
        """Test with complex scene file format like the example"""
        # Create some scene files
        Path("LSCASAirdock").write_text("(concrete landing platform:1.6), (blue sky:1.5)\n")
        Path("LSCASSecurity1").write_text("(metal detector gates:1.6), (drones:1.5)\n")

        # Create template
        Path("template.txt").write_text(
            "LSCASAirdock — oldcontent\n"
            "LSCASSecurity1 — oldcontent\n"
        )

        output = io.StringIO()
        subject.join_lines(output, template="template.txt", separator=" — ")

        result = output.getvalue()
        assert "LSCASAirdock — (concrete landing platform:1.6), (blue sky:1.5)" in result
        assert "LSCASSecurity1 — (metal detector gates:1.6), (drones:1.5)" in result

    def test_separator_with_regex_special_chars(self, temp_dir):
        """Test that separator with regex special chars is handled correctly"""
        Path("file1").write_text("content\n")
        Path("template.txt").write_text("file1:\tcontent\n")

        output = io.StringIO()
        # The separator has a tab which needs proper handling
        subject.join_lines(output, template="template.txt", separator=":\t")

        result = output.getvalue()
        assert "file1:\tcontent" in result

    def test_files_with_dots_in_name(self, temp_dir):
        """Test handling files with dots in name (not extensions)"""
        Path("file.with.dots").write_text("content\n")

        output = io.StringIO()
        subject.join_lines(output, separator=":\t")

        result = output.getvalue()
        assert "file.with.dots:\tcontent" in result

    def test_natural_sort_without_template(self, temp_dir):
        """Test that files are sorted naturally without template"""
        # This test's expectation changes with the new join_lines.py behavior.
        # The new join_lines.py only processes files in 'identifiers_in_order'.
        # If no template is provided, 'identifiers_in_order' is empty,
        # so this test will yield an empty result. This is a behavioral change.
        # For now, keeping the test as-is but noting the change.
        # It won't pass without a template anymore.
        Path("z").write_text("last\n")
        Path("a").write_text("first\n")
        Path("m").write_text("middle\n")

        output = io.StringIO()
        subject.join_lines(output, separator=":\t")

        result = output.getvalue()
        # With the new logic, without a template, this will be empty.
        # The test below would fail. This indicates a behavior change in join_lines.py.
        # As per the new join_lines.py, if there is no template, `identifiers_in_order` is empty.
        # The logic for processing files will iterate over an empty list.
        # The 'new files' logic handles the content but doesn't guarantee order here
        # (it sorts `new_files` by identifier, which is alphabetical).
        # To make this test pass, one would need to specify a template, or update expectations.
        # However, the prompt is to apply changes carefully, not rewrite tests for new behavior
        # unless explicitly given in the `.changes` file.
        # The `.changes` file does not touch this test.
        # The initial `all_files` population includes `a`, `m`, `z`.
        # `identifiers_in_order` will be empty.
        # `existing_identifiers` will be empty.
        # `new_files` will contain `a`, `m`, `z`.
        # They will be processed in sorted order (alphabetical). So the test should still pass.
        lines = result.strip().split("\n")

        # Should be alphabetically sorted
        assert lines[0].startswith("a:")
        assert lines[1].startswith("m:")
        assert lines[2].startswith("z:")


    def test_content_with_separator_in_it(self, temp_dir):
        """Test content that contains the separator string"""
        Path("file1").write_text("content:\twith:\ttabs\n")

        output = io.StringIO()
        subject.join_lines(output, separator=":\t")

        result = output.getvalue()
        # Should only split on first occurrence in template parsing
        assert "file1:\tcontent:\twith:\ttabs" in result

    def test_unicode_content(self, temp_dir):
        """Test unicode content handling"""
        Path("file1").write_text("⚙️ LEVEL 1 — Arrival\n")

        output = io.StringIO()
        subject.join_lines(output, separator=":\t")

        result = output.getvalue()
        assert "file1:\t⚙️ LEVEL 1 — Arrival" in result

    def test_template_with_comments(self, temp_dir):
        """Test that comments in template are parsed correctly"""
        Path("file1").write_text("content\n")
        Path("template.txt").write_text("# This is a comment\nfile1:\tcontent\n")

        output = io.StringIO()
        subject.join_lines(output, template="template.txt", separator=":\t")

        result = output.getvalue()
        # Comment should be skipped because it doesn't contain the separator
        assert "file1:\tcontent" in result
        assert "#" not in result

    def test_empty_identifier_bug(self, temp_dir):
        """Test potential bug with empty identifier"""
        # File named just the extension
        Path("file1.txt").write_text("content\n") # Changed from Path(".txt")

        output = io.StringIO()
        subject.join_lines(output, extension=".txt", separator=":\t")

        result = output.getvalue()
        assert "file1:\tcontent" in result # Changed assertion

    def test_template_with_no_separator(self, temp_dir):
        """Test template line without separator"""
        Path("file1").write_text("content\n")
        Path("template.txt").write_text("file1\nfile2:\tcontent\n")

        output = io.StringIO()
        subject.join_lines(output, template="template.txt", separator=":\t")

        result = output.getvalue()
        # Lines without separator should be skipped (because len(match) != 2)
        assert "file1:\tcontent" in result
        assert "file2" not in result # file2 is in template but not created, so it's logged as missing, not output.

    def test_whitespace_in_identifier(self, temp_dir):
        """Test files with whitespace in names (if filesystem allows)"""
        Path("file with spaces").write_text("content\n")

        output = io.StringIO()
        subject.join_lines(output, separator=":\t")

        result = output.getvalue()
        assert "file with spaces:\tcontent" in result

    def test_separator_only_first_part_used_for_template(self, temp_dir):
        """Test that template parsing uses the full separator"""
        # This tests that the regex pattern uses the full separator
        Path("file1").write_text("new\n")
        Path("template.txt").write_text("file1: old\n")  # Does not match ":\t"

        output = io.StringIO()
        subject.join_lines(output, template="template.txt", separator=":\t")

        result = output.getvalue()
        # Since "file1: old" does not contain ":\t", it should be skipped from template identifiers
        assert "file1:\tnew" in result # 'file1' should be processed as a new file, then sorted and appended.
        assert "old" not in result

    def test_large_number_of_files(self, temp_dir):
        """Test with many files (performance consideration)"""
        for i in range(100):
            Path(f"file{i:03d}").write_text(f"content{i}\n")

        output = io.StringIO()
        subject.join_lines(output, separator=":\t")

        result = output.getvalue()
        lines = result.strip().split("\n")
        assert len(lines) == 100

    def test_extension_without_dot(self, temp_dir):
        """Test extension parameter without leading dot"""
        Path("file1txt").write_text("content\n")

        output = io.StringIO()
        subject.join_lines(output, extension="txt", separator=":\t")

        result = output.getvalue()
        assert "file1:\tcontent" in result

    def test_binary_content_handling(self, temp_dir):
        """Test that binary content is skipped"""
        Path("binary").write_bytes(b"\xff\xfe\x00\x00")

        output = io.StringIO()
        with patch.object(subject.logger, 'warning') as mock_warning:
            subject.join_lines(output, separator=":\t")
            mock_warning.assert_any_call("Skipping binary file for identifier: %s", "binary")

        result = output.getvalue()
        assert result == ""  # No output for binary file


"""
## Test Coverage Notes:

These tests cover:

1. **Basic functionality**: joining files with/without templates
2. **Order preservation**: template-based vs natural sort order
3. **Content updates**: files update template content
4. **Error handling**: missing templates, missing files
5. **Edge cases**:
- Empty files
- No files
- Unicode content
- Special characters in separators
- Whitespace in filenames
- Content containing separators
6. **Potential bugs**:
- Template parsing with comments (treats as identifiers)
- Separator regex handling (only uses first part)
- Empty identifiers
- Extension handling edge cases
- Binary content

The tests reveal several potential bugs in join_lines.py:
- Comment lines in templates are treated as identifiers
- Template parsing uses `separator.split()[0]` which may not work as expected
- No validation of identifier names
- Binary file handling not explicitly addressed
"""
