import pytest
import io
from unittest.mock import patch
from func import process_source

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
    with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout, \
        patch('sys.stdin', new=io.StringIO(sample_python_code)):
        process_source("-", process_all=process_all, show_names=show_names)
        output = mock_stdout.getvalue().strip().split('\n')
        assert output == expected

def test_show_all_info(sample_python_code):
    with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout, \
        patch('sys.stdin', new=io.StringIO(sample_python_code)):
        process_source("-", "hello_world", show_all_info=True)
        output = mock_stdout.getvalue().strip()
        expected = "def hello_world():\n    '''Say hello to the world'''"
        assert output == expected

def test_show_decorators(sample_python_code):
    with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout, \
        patch('sys.stdin', new=io.StringIO(sample_python_code)):
        process_source("-", "decorated_function", show_decorators=True, show_names=True)
        output = mock_stdout.getvalue().strip()
        expected = "@decorator\ndecorated_function"
        assert output == expected

def test_list_mode(sample_python_code):
    with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout, \
        patch('sys.stdin', new=io.StringIO(sample_python_code)):
        process_source("-", list_mode=True)
        output = mock_stdout.getvalue().strip().split('\n')
        expected = ['hello_world', 'TestClass', 'TestClass.method', 'decorated_function']
        assert output == expected
