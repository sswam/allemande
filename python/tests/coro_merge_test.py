import pytest
import asyncio
import os
from unittest.mock import patch, MagicMock
from typing import Any

import coro_merge as subject

subject_name = subject.__name__

@pytest.fixture
def temp_files(tmp_path):
    file1 = tmp_path / "input1.txt"
    file2 = tmp_path / "input2.txt"
    output = tmp_path / "output.txt"
    return file1, file2, output

async def create_test_file(filename, content):
    async with subject.aiofiles.open(filename, 'w') as f:
        await f.write(content)

async def read_file_content(filename):
    async with subject.aiofiles.open(filename, 'r') as f:
        return await f.read()

@pytest.mark.asyncio
async def test_merge_empty_files(temp_files):
    file1, file2, output = temp_files
    await create_test_file(file1, "")
    await create_test_file(file2, "")

    await subject.merge(str(file1), str(file2), str(output))

    result = await read_file_content(output)
    assert result == ""

@pytest.mark.asyncio
async def test_merge_one_empty_file(temp_files):
    file1, file2, output = temp_files
    await create_test_file(file1, "apple\nbanana\n")
    await create_test_file(file2, "")

    await subject.merge(str(file1), str(file2), str(output))

    result = await read_file_content(output)
    assert result == "apple\nbanana\n"

@pytest.mark.asyncio
async def test_merge_sorted_files(temp_files):
    file1, file2, output = temp_files
    await create_test_file(file1, "apple\ncherry\ngrape\n")
    await create_test_file(file2, "banana\nkiwi\npeach\n")

    await subject.merge(str(file1), str(file2), str(output))

    result = await read_file_content(output)
    assert result == "apple\nbanana\ncherry\ngrape\nkiwi\npeach\n"

@pytest.mark.asyncio
async def test_merge_with_duplicates(temp_files):
    file1, file2, output = temp_files
    await create_test_file(file1, "apple\nbanana\ncherry\n")
    await create_test_file(file2, "banana\ncherry\ndate\n")

    await subject.merge(str(file1), str(file2), str(output))

    result = await read_file_content(output)
    assert result == "apple\nbanana\nbanana\ncherry\ncherry\ndate\n"

@pytest.mark.asyncio
async def test_merge_large_files(temp_files):
    file1, file2, output = temp_files
    await create_test_file(file1, "\n".join([f"item{i}" for i in range(0, 10000, 2)]) + "\n")
    await create_test_file(file2, "\n".join([f"item{i}" for i in range(1, 10000, 2)]) + "\n")

    await subject.merge(str(file1), str(file2), str(output))

    result = await read_file_content(output)
    assert len(result.splitlines()) == 10000
    assert result.startswith("item0\nitem1\nitem2\n")
    assert result.endswith("item9997\nitem9998\nitem9999\n")

@pytest.mark.asyncio
async def test_merger_simple():
    q1, q2, q_out = subject.Queue(), subject.Queue(), subject.Queue()

    for item in ['a', 'c', 'e']:
        await q1.put(item)
    await q1.put(None)

    for item in ['b', 'd', 'f']:
        await q2.put(item)
    await q2.put(None)

    await subject.merger_simple(q1.get, q2.get, q_out.put)

    result = []
    while True:
        item = await q_out.get()
        if item is None:
            break
        result.append(item)

    assert result == ['a', 'b', 'c', 'd', 'e', 'f']

@pytest.mark.asyncio
async def test_merger():
    q1, q2, q_out = subject.Queue(), subject.Queue(), subject.Queue()

    for item in ['a', 'c', 'e']:
        await q1.put(item)
    await q1.put(None)

    for item in ['b', 'd', 'f']:
        await q2.put(item)
    await q2.put(None)

    await subject.merger(q1.get, q2.get, q_out.put)

    result = []
    while True:
        item = await q_out.get()
        if item is None:
            break
        result.append(item)

    assert result == ['a', 'b', 'c', 'd', 'e', 'f']

@pytest.mark.asyncio
async def test_main(temp_files, capsys):
    file1, file2, output = temp_files
    await create_test_file(file1, "apple\ncherry\n")
    await create_test_file(file2, "banana\ndate\n")

    with patch('sys.argv', ['coro_merge.py', str(file1), str(file2), str(output)]):
        await subject.main()

    result = await read_file_content(output)
    assert result == "apple\nbanana\ncherry\ndate\n"

def test_version():
    assert hasattr(subject, '__version__')
    assert isinstance(subject.__version__, str)
