import os
import io
import pytest
from unittest.mock import patch, MagicMock

import diff_blocks as subject  # type: ignore

subject_name = subject.__name__


def create_test_files(content1, content2):
    with open('test1.py', 'w') as f:
        f.write(content1)
    with open('test2.py', 'w') as f:
        f.write(content2)


def delete_test_files():
    os.remove('test1.py')
    os.remove('test2.py')


def test_extract_blocks():
    lines = [
        "def function1():\n",
        "    print('Hello')\n",
        "    if True:\n",
        "        print('World')\n",
        "    print('Goodbye')\n",
    ]
    expected_blocks = [
        subject.Block(indent=0, start=1, end=5, lines=["def function1():\n"]),
        subject.Block(indent=4, start=2, end=5, lines=[
            "    print('Hello')\n",
            "    if True:\n",
            "    print('Goodbye')\n",
        ]),
        subject.Block(indent=8, start=4, end=4, lines=["        print('World')\n"]),
    ]
    result = subject.extract_blocks(lines)
    assert result == expected_blocks


def test_compare_blocks():
    block1 = [
        subject.Block(indent=4, start=1, end=2, lines=["    print('Hello')\n", "    print('World')\n"])
    ]
    block2 = [
        subject.Block(indent=4, start=1, end=2, lines=["    print('Hello')\n", "    print('Earth')\n"])
    ]
    diff = subject.compare_blocks(block1, block2)
    expected_diff = [
        '@@ -1,2 +1,2 @@',
        "-    print('Hello')",
        "-    print('World')",
        "+    print('Hello')",
        "+    print('Earth')",
    ]
    assert diff == expected_diff


def test_diff_blocks():
    content1 = "def function1():\n    print('Hello')\n    print('World')\n"
    content2 = "def function1():\n    print('Hello')\n    print('Earth')\n"
    create_test_files(content1, content2)

    diff = subject.diff_blocks('test1.py', 'test2.py')
    expected_diff = [
        '--- test1.py',
        '+++ test2.py',
        '@@ -1,3 +1,3 @@',
        '-def function1():',
        '-    print(\'Hello\')',
        '-    print(\'World\')',
        '+def function1():',
        '+    print(\'Hello\')',
        '+    print(\'Earth\')',
    ]
    assert diff == expected_diff

    delete_test_files()


def test_print_diff():
    diff = [
        '--- file1.py',
        '+++ file2.py',
        '@@ -1,2 +1,2 @@',
        "     print('Hello')",
        "-    print('World')",
        "+    print('Earth')",
    ]
    output_stream = io.StringIO()

    def mock_put(text):
        output_stream.write(text + '\n')

    subject.print_diff(diff, mock_put)
    output = output_stream.getvalue()
    assert '--- file1.py' in output
    assert '-    print(\'World\')' in output
    assert '+    print(\'Earth\')' in output


@patch(f'{subject_name}.diff_blocks')
@patch(f'{subject_name}.print_diff')
def test_main_diff(mock_print_diff, mock_diff_blocks):
    mock_diff_blocks.return_value = ["Mocked diff"]
    output_stream = io.StringIO()

    def mock_put(text):
        output_stream.write(text + '\n')

    subject.main_diff(mock_put, 'file1.py', 'file2.py')

    mock_diff_blocks.assert_called_once_with('file1.py', 'file2.py')
    mock_print_diff.assert_called_once_with(["Mocked diff"], mock_put)


# Test empty files
def test_empty_files():
    create_test_files("", "")
    diff = subject.diff_blocks('test1.py', 'test2.py')
    assert diff == ['--- test1.py', '+++ test2.py']
    delete_test_files()


# Test files with only whitespace differences
def test_whitespace_diff():
    content1 = "def func():\n    pass\n"
    content2 = "def func():\n\tpass\n"
    create_test_files(content1, content2)
    diff = subject.diff_blocks('test1.py', 'test2.py')
    assert len(diff) > 2  # There should be a difference due to indentation
    delete_test_files()


# Test large files
def test_large_files():
    content1 = "def func():\n    pass\n" * 1000
    content2 = "def func():\n    print('hello')\n" * 1000
    create_test_files(content1, content2)
    diff = subject.diff_blocks('test1.py', 'test2.py')
    assert len(diff) > 2
    delete_test_files()
