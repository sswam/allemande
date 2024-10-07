import os

# Disable DeprecationWarning https://github.com/jupyter/jupyter_core/issues/398
os.environ["JUPYTER_PLATFORM_DIRS"] = "1"

import io
import pytest
from unittest.mock import patch, MagicMock

import sh_deps as subject

subject_main = subject.sh_deps


def test_parse_script():
    script_content = """
    #!/bin/bash
    source /path/to/script.sh
    . ./relative_script.sh
    cat /etc/passwd
    echo "Hello, World!"
    ls | grep test
    result=$(date)
    echo `whoami`
    if [ -f /etc/hosts ]; then
        cat /etc/hosts
    fi
    """

    # Define which paths exist
    existing_paths = {
        "/path/to/script.sh",
        "/absolute/path",
        "/etc/passwd",
        "./relative_script.sh",
        "/etc/hosts",
    }

    # Mapping of commands to their executable paths
    executable_mapping = {
        "cat": "/bin/cat",
        "echo": "/bin/echo",
        "ls": "/bin/ls",
        "grep": "/bin/grep",
        "date": "/bin/date",
        "whoami": "/usr/bin/whoami",
    }

    def mock_exists(path):
        return path in existing_paths

    def mock_find_executable(cmd):
        return executable_mapping.get(cmd)

    with patch('os.path.exists', side_effect=mock_exists), \
         patch('sh_deps.find_executable', side_effect=mock_find_executable):
        deps = subject.parse_script(script_content)

    expected_deps = {
        "/path/to/script.sh",
        os.path.abspath("./relative_script.sh"),
        "/etc/passwd",
        "/etc/hosts",
        "/bin/cat",
        "/bin/echo",
        "/bin/ls",
        "/bin/grep",
        "/bin/date",
        "/usr/bin/whoami",
    }

    assert deps == expected_deps


def test_process_token():
    cwd = "/home/user"
    existing_files = {
        "/absolute/path",
        "/home/user/relative/path",
    }

    def mock_exists(path):
        return path in existing_files

    with patch('os.path.exists', side_effect=mock_exists):
        assert subject.process_token("/absolute/path", cwd) == {"/absolute/path"}
        assert subject.process_token("relative/path", cwd) == {os.path.abspath("/home/user/relative/path")}
        assert subject.process_token("-option", cwd) == set()
        assert subject.process_token("filename.sh", cwd) == set()  # Assuming it's not in tools_standard

def test_find_executable():
    # Define PATH for the test
    test_path = "/bin:/usr/bin"

    # Mapping of commands to their existence
    executable_mapping = {
        "/bin/ls": True,
        "/usr/bin/whoami": True,
        "/bin/nonexistent": False,
    }

    def mock_isfile(path):
        return executable_mapping.get(path, False)

    def mock_access(path, mode):
        return executable_mapping.get(path, False)

    with patch.dict("os.environ", {"PATH": test_path}), \
         patch("os.path.isfile", side_effect=mock_isfile), \
         patch("os.access", side_effect=mock_access):
        assert subject.find_executable("ls") == "/bin/ls"
        assert subject.find_executable("whoami") == "/usr/bin/whoami"
        assert subject.find_executable("nonexistent") is None


@pytest.mark.parametrize(
    "input_content, expected_output",
    [
        ("echo 'Hello'\ncat /etc/passwd", "/bin/cat\n/bin/echo\n/etc/passwd\n"),
        ("source /path/to/script.sh", "/path/to/script.sh\n"),
        ("ls | grep test", "/bin/grep\n/bin/ls\n"),
        ("result=$(date)", "/bin/date\n"),
        ("echo `whoami`", "/bin/echo\n/usr/bin/whoami\n"),
        ("if [ -f /etc/hosts ]; then\n    cat /etc/hosts\nfi", "/bin/cat\n/etc/hosts\n"),
    ],
)
def test_sh_deps(input_content, expected_output):
    input_stream = io.StringIO(input_content)
    output_stream = io.StringIO()

    # Define existing paths and executables
    existing_paths = {
        "/path/to/script.sh",
        "/etc/passwd",
        "/etc/hosts",
    }

    executable_mapping = {
        "echo": "/bin/echo",
        "cat": "/bin/cat",
        "ls": "/bin/ls",
        "grep": "/bin/grep",
        "date": "/bin/date",
        "whoami": "/usr/bin/whoami",
    }

    def mock_exists(path):
        # Only specific paths exist
        return path in existing_paths

    def mock_find_executable(cmd):
        return executable_mapping.get(cmd)

    with patch('os.path.exists', side_effect=mock_exists), \
         patch('sh_deps.find_executable', side_effect=mock_find_executable):
        subject_main(istream=input_stream, ostream=output_stream)

    assert output_stream.getvalue() == expected_output


@patch("builtins.open", new_callable=MagicMock)
def test_sh_deps_with_files(mock_open):
    mock_open.return_value.__enter__.return_value.read.return_value = "echo 'Hello'"
    output_stream = io.StringIO()

    # Define existing executables
    executable_mapping = {
        "echo": "/bin/echo",
    }

    def mock_exists(path):
        # Only the echo executable exists
        return path == "/bin/echo"

    def mock_find_executable(cmd):
        return executable_mapping.get(cmd)

    with patch('os.path.exists', side_effect=mock_exists), \
         patch('sh_deps.find_executable', side_effect=mock_find_executable):
        subject_main("test_script.sh", ostream=output_stream)

    assert output_stream.getvalue() == "/bin/echo\n"

if __name__ == "__main__":
    pytest.main([__file__])
