#!/usr/bin/env python3-allemande

"""Tests for atail.py"""

import io
import os
import tempfile
from pathlib import Path
import asyncio
import pytest
from unittest.mock import patch, MagicMock

import atail as subject

subject_name = subject.__name__

@pytest.fixture
def temp_file():
    """Create a temporary file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        yield f.name
    os.unlink(f.name)

@pytest.fixture
def empty_file(temp_file):
    """Create an empty temporary file."""
    Path(temp_file).touch()
    return temp_file

@pytest.fixture
def sample_file(temp_file):
    """Create a temporary file with sample content."""
    with open(temp_file, 'w') as f:
        f.write("line1\nline2\nline3\n")
    return temp_file

async def test_basic_tail_no_follow(sample_file):
    """Test basic tail functionality without follow."""
    output = io.StringIO()
    await subject.atail(output=output, filename=sample_file, lines=2)
    assert output.getvalue() == "line2\nline3\n"

async def test_tail_all_lines(sample_file):
    """Test tail with all_lines=True."""
    output = io.StringIO()
    await subject.atail(output=output, filename=sample_file, all_lines=True)
    assert output.getvalue() == "line1\nline2\nline3\n"

async def test_tail_empty_file(empty_file):
    """Test tailing an empty file."""
    output = io.StringIO()
    await subject.atail(output=output, filename=empty_file)
    assert output.getvalue() == ""

async def test_tail_nonexistent_file():
    """Test tailing a nonexistent file."""
    output = io.StringIO()
    with pytest.raises(FileNotFoundError):
        await subject.atail(output=output, filename="/nonexistent/file")

async def test_tail_zero_lines(sample_file):
    """Test tailing with lines=0."""
    output = io.StringIO()
    await subject.atail(output=output, filename=sample_file, lines=0)
    assert output.getvalue() == ""

@pytest.mark.asyncio
async def test_tail_with_rewind_string(sample_file):
    """Test tail with rewind string."""
    output = io.StringIO()
    rewind_msg = "=== FILE REWOUND ===\n"

    # Create a task that will run briefly then complete
    async def run_brief_tail():
        await subject.atail(
            output=output,
            filename=sample_file,
            rewind=True,
            rewind_string=rewind_msg,
            follow=True,
            lines=2
        )

    # Run for 0.1s then cancel
    task = asyncio.create_task(run_brief_tail())
    await asyncio.sleep(0.1)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

    # Verify we got some output
    assert len(output.getvalue()) > 0

def test_get_opts_default():
    """Test default command line options."""
    with patch('sys.argv', ['atail']):
        opts = subject.get_opts()
        assert opts.filename == subject.AsyncTail.DEFAULT_FILENAME
        assert not opts.wait_for_create
        assert opts.lines == 0
        assert not opts.all_lines
        assert not opts.follow
        assert not opts.rewind
        assert opts.rewind_string is None
        assert not opts.restart
        assert opts.poll is None

def test_get_opts_implied_follow():
    """Test that certain options imply --follow."""
    with patch('sys.argv', ['atail', '--rewind']):
        opts = subject.get_opts()
        assert opts.follow

    with patch('sys.argv', ['atail', '--restart']):
        opts = subject.get_opts()
        assert opts.follow

    with patch('sys.argv', ['atail', '--poll', '1.0']):
        opts = subject.get_opts()
        assert opts.follow

def test_get_opts_rewind_string_validation():
    """Test that --rewind-string requires --rewind."""
    with pytest.raises(SystemExit):
        with patch('sys.argv', ['atail', '--rewind-string', 'test']):
            subject.get_opts()

async def test_asynctail_context_manager(sample_file):
    """Test AsyncTail as a context manager."""
    async with subject.AsyncTail(filename=sample_file) as queue:
        assert isinstance(queue, asyncio.Queue)

async def test_asynctail_double_enter(sample_file):
    """Test that AsyncTail cannot be entered twice."""
    tail = subject.AsyncTail(filename=sample_file)
    async with tail:
        with pytest.raises(RuntimeError):
            async with tail:
                pass

if __name__ == '__main__':
    pytest.main([__file__])
