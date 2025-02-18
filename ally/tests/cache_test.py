import os
import pytest
from unittest.mock import patch, mock_open
import tempfile
import time
from typing import Any

from ally import cache as subject

subject_name = subject.__name__

def test_version():
    assert hasattr(subject, '__VERSION__')
    assert isinstance(subject.__VERSION__, str)

def test_cache_init():
    cache = subject.FileCache()
    assert isinstance(cache._cache, dict)
    assert isinstance(cache._last_modified, dict)
    assert len(cache._cache) == 0
    assert len(cache._last_modified) == 0

@pytest.fixture
def test_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        files = {
            'test.json': '{"key": "value"}',
            'test.yaml': 'key: value',
            'test.txt': 'hello world',
            'test.csv': 'a,b,c\n1,2,3',
            'test.tsv': 'a\tb\tc\n1\t2\t3'
        }
        for fname, content in files.items():
            with open(os.path.join(tmpdir, fname), 'w') as f:
                f.write(content)
        yield tmpdir

def test_load_formats(test_files):
    cache = subject.FileCache()

    # Test JSON
    json_path = os.path.join(test_files, 'test.json')
    assert cache.load(json_path) == {"key": "value"}

    # Test YAML
    yaml_path = os.path.join(test_files, 'test.yaml')
    assert cache.load(yaml_path) == {"key": "value"}

    # Test TXT
    txt_path = os.path.join(test_files, 'test.txt')
    assert cache.load(txt_path) == "hello world"

    # Test CSV
    csv_path = os.path.join(test_files, 'test.csv')
    assert cache.load(csv_path) == [['a', 'b', 'c'], ['1', '2', '3']]

    # Test TSV
    tsv_path = os.path.join(test_files, 'test.tsv')
    assert cache.load(tsv_path) == [['a', 'b', 'c'], ['1', '2', '3']]

def test_load_invalid_format():
    cache = subject.FileCache()
    # Create temp file first
    with tempfile.NamedTemporaryFile(suffix='.invalid') as tf:
        with pytest.raises(ValueError):
            cache.load(tf.name)

def test_save_and_load(test_files):
    cache = subject.FileCache()
    path = os.path.join(test_files, 'new.json')
    data = {"test": "data"}

    cache.save(path, data)
    loaded_data = cache.load(path)
    assert loaded_data == data

def test_cache_modification_tracking(test_files):
    cache = subject.FileCache()
    path = os.path.join(test_files, 'test.json')

    # First load
    initial_data = cache.load(path)

    # Second load should use cache
    with patch('builtins.open', mock_open()) as mock_file:
        cached_data = cache.load(path)
        mock_file.assert_not_called()

    assert initial_data == cached_data

def test_noclobber(test_files):
    cache = subject.FileCache()
    path = os.path.join(test_files, 'test.json')

    # Load file
    cache.load(path)

    # Simulate external modification
    time.sleep(0.1)  # Ensure mtime changes
    with open(path, 'w') as f:
        f.write('{"modified": "externally"}')

    # Attempt to save should raise error
    with pytest.raises(FileExistsError):
        cache.save(path, {"new": "content"})

def test_clear_cache():
    cache = subject.FileCache()
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json') as tf:
        tf.write('{"test": "data"}')
        tf.flush()

        # Load file
        cache.load(tf.name)
        assert len(cache._cache) == 1

        # Clear specific path
        cache.clear(tf.name)
        assert len(cache._cache) == 0

        # Load again and clear all
        cache.load(tf.name)
        cache.clear()
        assert len(cache._cache) == 0

def test_deep_compare():
    cache = subject.FileCache()

    # Test basic types
    assert cache._deep_compare(1, 1)
    assert not cache._deep_compare(1, 2)
    assert cache._deep_compare("a", "a")
    assert not cache._deep_compare("a", "b")

    # Test lists
    assert cache._deep_compare([1, 2], [1, 2])
    assert not cache._deep_compare([1, 2], [2, 1])

    # Test dicts
    assert cache._deep_compare({"a": 1}, {"a": 1})
    assert not cache._deep_compare({"a": 1}, {"a": 2})

    # Test nested structures
    assert cache._deep_compare(
        {"a": [1, {"b": 2}]},
        {"a": [1, {"b": 2}]}
    )

def test_empty_and_none_cases():
    cache = subject.FileCache()

    # Test empty file handling
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt') as tf:
        loaded = cache.load(tf.name)
        assert loaded == ""

    # Test clearing non-existent path
    cache.clear("nonexistent.txt")  # Should not raise error
