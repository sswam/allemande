#!/usr/bin/env python3

"""Tests for split_lines.py"""

import io
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open
import tempfile
import os

import split_lines as subject  # type: ignore

subject_name = subject.__name__


def test_split_lines_basic(tmp_path):
    """Test basic splitting of lines."""
    os.chdir(tmp_path)

    input_text = "file1: content1\nfile2: content2\nfile3: content3\n"
    input_file = io.StringIO(input_text)

    subject.split_lines(input_file)

    assert Path("file1").read_text() == "content1\n"
    assert Path("file2").read_text() == "content2\n"
    assert Path("file3").read_text() == "content3\n"


def test_split_lines_with_extension(tmp_path):
    """Test splitting with file extension."""
    os.chdir(tmp_path)

    input_text = "file1: content1\nfile2: content2\n"
    input_file = io.StringIO(input_text)

    subject.split_lines(input_file, extension=".txt")

    assert Path("file1.txt").read_text() == "content1\n"
    assert Path("file2.txt").read_text() == "content2\n"
    assert not Path("file1").exists()
    assert not Path("file2").exists()


def test_split_lines_custom_pattern(tmp_path):
    """Test splitting with custom pattern."""
    os.chdir(tmp_path)

    input_text = "file1|content1\nfile2|content2\n"
    input_file = io.StringIO(input_text)

    subject.split_lines(input_file, pattern=r"\|")

    assert Path("file1").read_text() == "content1\n"
    assert Path("file2").read_text() == "content2\n"


def test_split_lines_whitespace_pattern(tmp_path):
    """Test splitting with whitespace in pattern."""
    os.chdir(tmp_path)

    input_text = "file1:   content with spaces\nfile2:\tcontent with tab\n"
    input_file = io.StringIO(input_text)

    subject.split_lines(input_file)

    assert Path("file1").read_text() == "content with spaces\n"
    assert Path("file2").read_text() == "content with tab\n"


def test_split_lines_skip_comments(tmp_path):
    """Test that comments are skipped by default."""
    os.chdir(tmp_path)

    input_text = "# comment line\nfile1: content1\n# another comment\nfile2: content2\n"
    input_file = io.StringIO(input_text)

    subject.split_lines(input_file)

    assert Path("file1").read_text() == "content1\n"
    assert Path("file2").read_text() == "content2\n"
    assert not Path("# comment line").exists()


def test_split_lines_with_comments(tmp_path):
    """Test that comments are processed when flag is set."""
    os.chdir(tmp_path)

    input_text = "#comment: content\nfile1: content1\n"
    input_file = io.StringIO(input_text)

    subject.split_lines(input_file, comments=True)

    assert Path("#comment").read_text() == "content\n"
    assert Path("file1").read_text() == "content1\n"


def test_split_lines_malformed_lines(tmp_path):
    """Test handling of malformed lines without separator."""
    os.chdir(tmp_path)

    input_text = "file1: content1\nmalformed line\nfile2: content2\n"
    input_file = io.StringIO(input_text)

    subject.split_lines(input_file)

    assert Path("file1").read_text() == "content1\n"
    assert Path("file2").read_text() == "content2\n"
    assert not Path("malformed line").exists()


def test_split_lines_empty_identifier(tmp_path):
    """Test handling of lines with empty identifier."""
    os.chdir(tmp_path)

    input_text = "file1: content1\n: empty identifier\nfile2: content2\n"
    input_file = io.StringIO(input_text)

    subject.split_lines(input_file)

    assert Path("file1").read_text() == "content1\n"
    assert Path("file2").read_text() == "content2\n"
    # Empty identifier should be skipped


def test_split_lines_empty_content(tmp_path):
    """Test handling of lines with empty content."""
    os.chdir(tmp_path)

    input_text = "file1: \nfile2: content2\n"
    input_file = io.StringIO(input_text)

    subject.split_lines(input_file)

    assert Path("file1").read_text() == "\n"
    assert Path("file2").read_text() == "content2\n"


def test_split_lines_empty_input(tmp_path):
    """Test handling of empty input."""
    os.chdir(tmp_path)

    input_file = io.StringIO("")

    subject.split_lines(input_file)

    # Should not create any files
    assert list(Path(".").glob("*")) == []


def test_split_lines_single_line(tmp_path):
    """Test handling of single line input."""
    os.chdir(tmp_path)

    input_text = "onlyfile: onlycontent\n"
    input_file = io.StringIO(input_text)

    subject.split_lines(input_file)

    assert Path("onlyfile").read_text() == "onlycontent\n"


def test_split_lines_overwrites_existing(tmp_path):
    """Test that existing files are overwritten."""
    os.chdir(tmp_path)

    # Create existing file
    Path("file1").write_text("old content\n")

    input_text = "file1: new content\n"
    input_file = io.StringIO(input_text)

    subject.split_lines(input_file)

    assert Path("file1").read_text() == "new content\n"


def test_split_lines_special_characters_in_identifier(tmp_path):
    """Test identifiers with special characters."""
    os.chdir(tmp_path)

    input_text = "file-name_123: content\n"
    input_file = io.StringIO(input_text)

    subject.split_lines(input_file)

    assert Path("file-name_123").read_text() == "content\n"


def test_split_lines_special_characters_in_content(tmp_path):
    """Test content with special characters."""
    os.chdir(tmp_path)

    input_text = "file1: content with: colon and\ttab\n"
    input_file = io.StringIO(input_text)

    subject.split_lines(input_file)

    assert Path("file1").read_text() == "content with: colon and\ttab\n"


def test_split_lines_multiline_behavior(tmp_path):
    """Test that each line creates a separate file (no multiline content)."""
    os.chdir(tmp_path)

    input_text = "file1: line1\nfile1: line2\n"
    input_file = io.StringIO(input_text)

    subject.split_lines(input_file)

    # Second line should overwrite the first
    assert Path("file1").read_text() == "line2\n"


def test_split_lines_no_trailing_newline_in_input(tmp_path):
    """Test input without trailing newline."""
    os.chdir(tmp_path)

    input_text = "file1: content1"
    input_file = io.StringIO(input_text)

    subject.split_lines(input_file)

    assert Path("file1").read_text() == "content1\n"


def test_split_lines_only_separator(tmp_path):
    """Test line with only separator."""
    os.chdir(tmp_path)

    input_text = ": \n"
    input_file = io.StringIO(input_text)

    subject.split_lines(input_file)

    # Empty identifier should be skipped
    files = list(Path(".").glob("*"))
    assert len(files) == 0


def test_split_lines_multiple_separators(tmp_path):
    """Test that only first separator is used for splitting."""
    os.chdir(tmp_path)

    input_text = "file1: content: with: more: colons\n"
    input_file = io.StringIO(input_text)

    subject.split_lines(input_file)

    assert Path("file1").read_text() == "content: with: more: colons\n"


def test_split_lines_pattern_with_groups(tmp_path):
    """Test pattern with regex groups."""
    os.chdir(tmp_path)

    input_text = "file1 = content1\nfile2 = content2\n"
    input_file = io.StringIO(input_text)

    subject.split_lines(input_file, pattern=r"\s*=\s*")

    assert Path("file1").read_text() == "content1\n"
    assert Path("file2").read_text() == "content2\n"


@patch('split_lines.logger')
def test_split_lines_logging(mock_logger, tmp_path):
    """Test that appropriate logging occurs."""
    os.chdir(tmp_path)

    input_text = "file1: content1\nmalformed\n# comment\n"
    input_file = io.StringIO(input_text)

    subject.split_lines(input_file)

    # Should log info about processed and skipped lines
    mock_logger.info.assert_called()
    mock_logger.debug.assert_called()


def test_split_lines_oserror_handling(tmp_path):
    """Test handling of OS errors when writing files."""
    os.chdir(tmp_path)

    input_text = "file1: content1\n"
    input_file = io.StringIO(input_text)

    with patch('pathlib.Path.write_text', side_effect=OSError("Disk full")):
        with pytest.raises(OSError):
            subject.split_lines(input_file)


def test_split_lines_unicode_content(tmp_path):
    """Test handling of Unicode characters."""
    os.chdir(tmp_path)

    input_text = "file1: こんにちは世界\nfile2: 🎉emoji🎊\n"
    input_file = io.StringIO(input_text)

    subject.split_lines(input_file)

    assert Path("file1").read_text() == "こんにちは世界\n"
    assert Path("file2").read_text() == "🎉emoji🎊\n"


def test_split_lines_long_content(tmp_path):
    """Test handling of very long content."""
    os.chdir(tmp_path)

    long_content = "x" * 10000
    input_text = f"file1: {long_content}\n"
    input_file = io.StringIO(input_text)

    subject.split_lines(input_file)

    assert Path("file1").read_text() == f"{long_content}\n"


def test_split_lines_many_files(tmp_path):
    """Test splitting into many files."""
    os.chdir(tmp_path)

    lines = [f"file{i}: content{i}\n" for i in range(100)]
    input_text = "".join(lines)
    input_file = io.StringIO(input_text)

    subject.split_lines(input_file)

    for i in range(100):
        assert Path(f"file{i}").read_text() == f"content{i}\n"


def test_setup_args():
    """Test that setup_args configures arguments correctly."""
    args = []

    def mock_arg(*args_tuple, **kwargs):
        args.append((args_tuple, kwargs))

    subject.setup_args(mock_arg)

    assert len(args) == 4
    assert args[0][0][0] == 'input_file'
    assert args[1][0] == ('--pattern', '-p')
    assert args[2][0] == ('--extension', '-x')
    assert args[3][0] == ('--comments', '-c')
