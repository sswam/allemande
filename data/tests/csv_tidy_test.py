#!/usr/bin/env python3-allemande

import io
import pytest
from typing import TextIO, Iterator

import csv_tidy as subject

subject_name = subject.__name__

def make_reader(content: str, **kwargs) -> Iterator[list[str]]:
    """Helper function to create a CSV reader from a string."""
    return subject.reader(io.StringIO(content), **kwargs)

def test_empty_file():
    reader = make_reader("")
    assert list(reader) == []

def test_empty_lines():
    reader = make_reader("\n\n\n")
    assert list(reader) == [[""], [""], [""]]

@pytest.mark.parametrize("input_str, expected", [
    ("a", [["a"]]),
    ("a,b", [["a", "b"]]),
    ("a,b,c", [["a", "b", "c"]]),
])
def test_simple_fields(input_str, expected):
    reader = make_reader(input_str)
    assert list(reader) == expected

@pytest.mark.parametrize("input_str, expected", [
    (" a ", [["a"]]),
    ("a , b", [["a", "b"]]),
    (" a , b , c ", [["a", "b", "c"]]),
])
def test_whitespace_stripping(input_str, expected):
    reader = make_reader(input_str)
    assert list(reader) == expected

@pytest.mark.parametrize("input_str, expected", [
    ('"a"', [["a"]]),
    ('" a "', [[" a "]]),  # Whitespace preserved in quoted fields
    ('"a,b"', [["a,b"]]),
    ('"a","b"', [["a", "b"]]),
])
def test_quoted_fields(input_str, expected):
    reader = make_reader(input_str)
    assert list(reader) == expected

def test_mixed_quoted_unquoted():
    reader = make_reader(' a ,"b", c ')
    assert list(reader) == [["a", "b", "c"]]

@pytest.mark.parametrize("input_str, expected", [
    ('""', [[""]]),
    ('" "', [[" "]]),
    ('"","",""', [["", "", ""]]),
])
def test_empty_quoted_fields(input_str, expected):
    reader = make_reader(input_str)
    assert list(reader) == expected

def test_double_quotes():
    reader = make_reader('"a""b"')
    assert list(reader) == [['a"b']]

def test_escaped_quotes():
    reader = make_reader(r'"a\"b"', escapechar='\\', doublequote=False)
    assert list(reader) == [['a"b']]

def test_multiple_lines():
    reader = make_reader("a,b\nc,d\ne,f")
    assert list(reader) == [["a", "b"], ["c", "d"], ["e", "f"]]

def test_custom_quote_char():
    reader = make_reader("'a','b'", quotechar="'")
    assert list(reader) == [["a", "b"]]

def test_tsv_format():
    content = "1\t2\t3\nA\tB\tC"
    reader = make_reader(content, delimiter="\t")
    assert list(reader) == [["1", "2", "3"], ["A", "B", "C"]]

def test_quoted_newlines():
    content = '"1,2\n3,4",b\nc,d'
    reader = make_reader(content)
    assert list(reader) == [["1,2\n3,4", "b"], ["c", "d"]]

def test_quoted_delimiters():
    content = '1,"2,3",4'
    reader = make_reader(content)
    assert list(reader) == [["1", "2,3", "4"]]

def test_empty_trailing_fields():
    reader = make_reader("a,b,,\nc,d,")
    assert list(reader) == [["a", "b", "", ""], ["c", "d", ""]]

def test_preserve_internal_whitespace():
    reader = make_reader('"  a  b  ","  c  "')
    assert list(reader) == [["  a  b  ", "  c  "]]

def test_iterator_protocol():
    reader = subject.CSVReader(io.StringIO("a,b\nc,d"))
    row = next(reader)
    assert row == ["a", "b"]
    row = next(reader)
    assert row == ["c", "d"]
    with pytest.raises(StopIteration):
        next(reader)

@pytest.mark.parametrize("input_str", [
    '"unclosed quote',
    '"unescaped " quote"',
])
def test_malformed_quoted(input_str):
    reader = make_reader(input_str)
    with pytest.raises(ValueError):
        list(reader)

@pytest.mark.parametrize("input_str", [
    '"escape at end\\"',
])
def test_malformed_escaped(input_str):
    reader = make_reader(input_str, escapechar='\\')
    with pytest.raises(ValueError):
        list(reader)

def test_large_file():
    # Create a large CSV file in memory
    large_content = "field1,field2,field3\n" * 1000
    reader = make_reader(large_content)
    row_count = sum(1 for _ in reader)
    assert row_count == 1000

def test_performance():
    # Basic performance test
    import time
    large_content = "field1,field2,field3\n" * 10000
    start_time = time.time()
    reader = make_reader(large_content)
    list(reader)
    elapsed = time.time() - start_time
    assert elapsed < 1.0  # Should process 10000 rows in less than a second
