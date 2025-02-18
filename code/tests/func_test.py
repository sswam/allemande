import pytest
import io
from unittest.mock import patch

# add parent to search path
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import func as subject

@pytest.fixture
def sample_python_code():
    return """
def hello_world():
    '''Say hello to the world'''
    print("Hello, World!")

class TestClass:
    def method(self):
        pass

@decorator
def decorated_function():
    pass
"""

@pytest.mark.parametrize("process_all, show_names, expected", [
    (True, True, ['hello_world', 'TestClass', 'TestClass.method', 'decorated_function']),
    (False, False, [])
])
def test_process_all(sample_python_code, process_all, show_names, expected):
    ostream = io.StringIO()
    istream = io.StringIO(sample_python_code)
    subject.func(istream, ostream, "-", process_all=process_all, show_names=show_names)
    lines = ostream.getvalue().strip().split('\n')
    actual = [line for line in lines if line]  # Remove empty lines
    assert actual == expected

def test_show_all_info(sample_python_code):
    ostream = io.StringIO()
    istream = io.StringIO(sample_python_code)
    subject.func(istream, ostream, "-", "hello_world", show_info=True, show_docstrings=True)
    result = ostream.getvalue().strip()
    expected = 'def hello_world():\n    """Say hello to the world"""'
    assert result == expected

def test_show_decorators(sample_python_code):
    ostream = io.StringIO()
    istream = io.StringIO(sample_python_code)
    subject.func(istream, ostream, "-", "decorated_function", show_decorators=True, show_names=True)
    result = ostream.getvalue().strip()
    expected = "@decorator\ndecorated_function"
    assert result == expected

def test_list_mode(sample_python_code):
    ostream = io.StringIO()
    istream = io.StringIO(sample_python_code)
    subject.func(istream, ostream, "-", list_mode=True)
    lines = ostream.getvalue().strip().split('\n')
    actual = [line for line in lines if line]
    expected = ['hello_world', 'TestClass', 'TestClass.method', 'decorated_function']
    assert actual == expected

def test_nested_function():
    nested_code = """
def outer():
    def inner():
        pass
    inner()
"""
    ostream = io.StringIO()
    istream = io.StringIO(nested_code)
    subject.func(istream, ostream, "-", "outer.inner", show_names=True)
    result = ostream.getvalue().strip()
    assert result == "outer.inner"
