import io
import pytest
from unittest.mock import patch, MagicMock
from typing import Any

import yody as subject  # type: ignore

subject_name = subject.__name__

def test_read_yody_basic():
    input_text = "key: value\nlist:\n  - item1\n  - item2\n\nBody text here"
    input_stream = io.StringIO(input_text)
    header, body = subject.read_yody(input_stream)

    assert header == {"key": "value", "list": ["item1", "item2"]}
    assert body == "Body text here"

def test_read_yody_empty_body():
    input_text = "key: value\n\n"
    input_stream = io.StringIO(input_text)
    header, body = subject.read_yody(input_stream)

    assert header == {"key": "value"}
    assert body == ""

def test_read_yody_minimal():
    input_text = "{}\n\nBody"
    input_stream = io.StringIO(input_text)
    header, body = subject.read_yody(input_stream)

    assert header == {}
    assert body == "Body"

@pytest.mark.parametrize("invalid_input", [
    "",  # Empty input
    "not yaml",  # No separator
    "key: value",  # No separator
    "[]\n\nBody",  # Header not a dict
    "invalid: :\n\nBody",  # Invalid YAML
])
def test_read_yody_invalid(invalid_input):
    input_stream = io.StringIO(invalid_input)
    with pytest.raises(ValueError):
        subject.read_yody(input_stream)

def test_write_yody_basic():
    header = {"key": "value", "list": ["item1", "item2"]}
    body = "Body text here"
    output_stream = io.StringIO()

    subject.write_yody(header, body, output_stream)
    output = output_stream.getvalue()

    # Verify we can read back what we wrote
    input_stream = io.StringIO(output)
    read_header, read_body = subject.read_yody(input_stream)

    assert read_header == header
    assert read_body == body

def test_write_yody_empty():
    header = {}
    body = ""
    output_stream = io.StringIO()

    subject.write_yody(header, body, output_stream)
    output = output_stream.getvalue()

    assert output == "{}\n\n"

def test_yody_integration():
    input_text = "key: value\n\nBody text"
    input_stream = io.StringIO(input_text)
    output_stream = io.StringIO()

    subject.yody(input_stream, output_stream)
    output = output_stream.getvalue()

    # Verify output can be read back correctly
    result_stream = io.StringIO(output)
    header, body = subject.read_yody(result_stream)

    assert header == {"key": "value"}
    assert body == "Body text"

