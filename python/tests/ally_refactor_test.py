import io
import pytest
from unittest.mock import patch, MagicMock
from typing import Any

import ally_refactor as subject  # type: ignore

subject_name = subject.__name__

def test_remove_argh_imports():
    code = """
import argh
from argh import arg
import os
    """
    expected = """
import os
    """
    assert subject.remove_argh_imports(code).strip() == expected.strip()

def test_change_main_call():
    code = """
if __name__ == "__main__":
    main.run(my_func)
    """
    expected = """
if __name__ == "__main__":
    main.go(my_func, setup_args)
    """
    assert subject.change_main_call(code, "my_func").strip() == expected.strip()

def test_extract_arg_decorators():
    code = """
@arg('--name', help='Your name')
@arg('--age', type=int, help='Your age')
def my_func(name, age):
    pass
    """
    expected = [
        (["'--name'"], {"help": "'Your name'"}),
        (["'--age'"], {"type": "int", "help": "'Your age'"})
    ]
    assert subject.extract_arg_decorators(code) == expected

def test_create_setup_args_function():
    arg_decorators = [
        (["'--name'"], {"help": "'Your name'"}),
        (["'--age'"], {"type": "int", "help": "'Your age'"})
    ]
    expected = """def setup_args(arg):
    \"\"\"Set up the command-line arguments.\"\"\"
    arg('--name', help='Your name')
    arg('--age', type=int, help='Your age')
"""
    assert subject.create_setup_args_function(arg_decorators) == expected

def test_update_main_function_signature():
    code = """
def main():
    print("Hello, World!")
    """
    expected = """
def main(get: geput.Get, put: geput.Put):
    print = geput.print(put)
    print("Hello, World!")
"""
    assert subject.update_main_function_signature(code).strip() == expected.strip()

def test_apply_part1_transforms():
    code = """
import argh
from argh import arg

@arg('--name', help='Your name')
def main(name):
    print(f"Hello, {name}!")

if __name__ == "__main__":
    main.run(main)
    """
    expected = """
def main(name, get: geput.Get, put: geput.Put):
    print = geput.print(put)
    print(f"Hello, {name}!")

def setup_args(arg):
    \"\"\"Set up the command-line arguments.\"\"\"
    arg('--name', help='Your name')

if __name__ == "__main__":
    main.go(main, setup_args)
"""
    assert subject.apply_part1_transforms(code).strip() == expected.strip()

def test_update_io_interface():
    code = """
from ally import main, logs

def my_func():
    data = get()
    all_data = get(all=True)
    put("Hello")
    """
    expected = """
from ally import main, logs, geput

def my_func(get: geput.Get, put: geput.Put):
    data = input()
    all_data = geput.whole(get)
    print("Hello")
    """
    assert subject.update_io_interface(code).strip() == expected.strip()

def test_refactor_code():
    code = """
import argh
from argh import arg
from ally import main, logs

@arg('--name', help='Your name')
def main(name):
    data = get()
    all_data = get(all=True)
    put(f"Hello, {name}!")

if __name__ == "__main__":
    main.run(main)
    """
    expected = """
from ally import main, logs, geput

def main(name, get: geput.Get, put: geput.Put):
    print = geput.print(put)
    data = input()
    all_data = geput.whole(get)
    print(f"Hello, {name}!")

def setup_args(arg):
    \"\"\"Set up the command-line arguments.\"\"\"
    arg('--name', help='Your name')

if __name__ == "__main__":
    main.go(main, setup_args)
"""
    assert subject.refactor_code(code).strip() == expected.strip()

def test_ally_refactor():
    input_code = """
def main():
    put("Hello, World!")

if __name__ == "__main__":
    main()
    """
    expected_output = """
from ally import geput

def main(get: geput.Get, put: geput.Put):
    print = geput.print(put)
    print("Hello, World!")

if __name__ == "__main__":
    main()
"""
    input_stream = io.StringIO(input_code)
    output_stream = io.StringIO()

    def mock_get():
        return input_stream.readline()

    def mock_put(text):
        output_stream.write(text)

    subject.ally_refactor(get=mock_get, put=mock_put)

    assert output_stream.getvalue().strip() == expected_output.strip()

def test_ally_refactor_error_handling():
    input_code = "invalid python code"
    input_stream = io.StringIO(input_code)
    output_stream = io.StringIO()

    def mock_get():
        return input_stream.readline()

    def mock_put(text):
        output_stream.write(text)

    with pytest.raises(Exception):
        subject.ally_refactor(get=mock_get, put=mock_put)

def test_setup_args():
    mock_arg = MagicMock()
    subject.setup_args(mock_arg)
    mock_arg.assert_not_called()
