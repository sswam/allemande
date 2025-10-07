import io
import pytest
import time
# from unittest.mock import patch, MagicMock
# from typing import Any

from ally import yaml as subject

# subject_name = subject.__name__

def test_yaml_create():
    # Test default creation
    yaml = subject.create()
    assert not yaml._fast_write

    # Test fast write creation
    yaml = subject.create(fast_write=True)
    assert yaml._fast_write

def test_yaml_set_fast_write():
    yaml = subject.create()
    assert not yaml._fast_write

    yaml.set_fast_write(True)
    assert yaml._fast_write

    yaml.set_fast_write(False)
    assert not yaml._fast_write

@pytest.mark.parametrize("test_data", [
    {},  # Empty dict
    [],  # Empty list
    "",  # Empty string
    {"key": "value"},  # Simple dict
    ["item1", "item2"],  # Simple list
    {"nested": {"key": "value"}},  # Nested dict
    {"multiline": "line1\nline2\nline3"},  # Multiline string
    None,  # None value
    42,  # Number
    True,  # Boolean
])
def test_yaml_dump_load_roundtrip(test_data):
    yaml = subject.create()

    # Test dump to string
    output = yaml.dump(test_data)
    assert output is not None

    # Test load from string
    loaded = yaml.load(output)
    assert loaded == test_data

def test_yaml_dump_to_stream():
    yaml = subject.create()
    test_data = {"key": "value"}

    # Test dump to stream
    stream = io.StringIO()
    yaml.dump(test_data, stream)
    assert "key: value" in stream.getvalue()

def test_yaml_load_from_stream():
    yaml = subject.create()
    test_data = "key: value"

    # Test load from stream
    stream = io.StringIO(test_data)
    loaded = yaml.load(stream)
    assert loaded == {"key": "value"}

def test_multiline_string_formatting():
    yaml = subject.create()
    test_data = {"multiline": "line1\nline2\nline3"}

    output = yaml.dump(test_data)
    assert "|" in output  # Should use literal style for multiline strings

def test_module_level_functions():
    test_data = {"key": "value"}

    # Test module-level dump
    output = subject.dump(test_data)
    assert output is not None

    # Test module-level load
    loaded = subject.load(output)
    assert loaded == test_data

    # Test module-level safe_load
    safely_loaded = subject.safe_load(output)
    assert safely_loaded == test_data

@pytest.mark.parametrize("fast_write", [True, False])
def test_yaml_dump_modes(fast_write):
    yaml = subject.create(fast_write=fast_write)
    test_data = {"key": "value"}

    output = yaml.dump(test_data)
    assert output is not None
    assert "key: value" in output

def test_yaml_invalid_input():
    yaml = subject.create()

    # Test loading invalid YAML
    with pytest.raises(Exception):
        yaml.load("invalid: yaml: : :")

    # Test loading empty input
    assert yaml.load("") is None

@pytest.mark.parametrize("test_data", [
    {"ordered": {"b": 2, "a": 1, "c": 3}},
    {"list": [3, 1, 2]},
])
def test_yaml_ordering(test_data):
    yaml = subject.create()
    output = yaml.dump(test_data)
    loaded = yaml.load(output)
    assert loaded == test_data

def test_yaml_indentation():
    yaml = subject.create()
    test_data = {
        "level1": {
            "level2": {
                "level3": "value"
            }
        }
    }
    output = yaml.dump(test_data)
    assert "  level2:" in output  # Check indentation
    assert "    level3:" in output

@pytest.mark.flaky
def test_yaml_performance():
    yaml_fast = subject.create(fast_write=True)
    yaml_careful = subject.create(fast_write=False)

    large_data = {"item" + str(i): "value" + str(i) for i in range(1000)}

    start = time.time()
    yaml_fast.dump(large_data)
    fast_time = time.time() - start

    start = time.time()
    yaml_careful.dump(large_data)
    careful_time = time.time() - start

    assert fast_time < careful_time
