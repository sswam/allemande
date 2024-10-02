import os

# disable DeprecationWarning https://github.com/jupyter/jupyter_core/issues/398
os.environ["JUPYTER_PLATFORM_DIRS"] = "1"

import io
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

import indent_split as subject
subject_main = subject.indent_split

def test_split_content():
    content = [
        "root:",
        "  level1:",
        "    level2:",
        "      level3:",
        "  another_level1:",
        "    another_level2:",
    ]

    # Test with line count
    sections = subject.split_content(content, max_count=3, min_count=2, use_chars=False)
    assert len(sections) == 2
    assert sections[0] == content[:3]
    assert sections[1] == content[3:]

    # Test with character count
    sections = subject.split_content(content, max_count=30, min_count=15, use_chars=True)
    assert len(sections) == 3

@pytest.mark.parametrize("max_count, min_count, chars, expected_sections", [
    (3, 2, False, 2),  # Line count
    (30, 15, True, 3),  # Character count
])
def test_indent_split(max_count, min_count, chars, expected_sections):
    input_content = """
root:
level1:
    level2:
    level3:
another_level1:
    another_level2:
"""
    input_stream = io.StringIO(input_content)
    output_stream = io.StringIO()

    with patch('pathlib.Path.mkdir'), \
        patch('builtins.open', MagicMock()), \
        patch('indent_split.logger') as mock_logger:

        subject_main(
            out_path='test_split.txt',
            max_count=max_count,
            min_count=min_count,
            istream=input_stream,
            ostream=output_stream,
            chars=chars,
            force=True
        )

    assert mock_logger.info.call_count == expected_sections + 1
    assert f"Split into {expected_sections} sections" in mock_logger.info.call_args_list[-1][0][0]

def test_indent_split_file_exists():
    input_content = "root:\n  level1:\n"
    input_stream = io.StringIO(input_content)
    output_stream = io.StringIO()

    with patch('pathlib.Path.mkdir'), \
        patch('builtins.open', side_effect=FileExistsError), \
        patch('indent_split.logger') as mock_logger:

        subject_main(
            out_path='test_split.txt',
            istream=input_stream,
            ostream=output_stream,
            force=False
        )

    assert "File test_split_000001.txt already exists. Use --force to overwrite." in mock_logger.warning.call_args[0][0]
