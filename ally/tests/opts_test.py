import argparse
import logging
import inspect

import pytest

from ally import opts as subject

subject_name = subject.__name__

__version__ = "0.1.5"


def test_CustomHelpFormatter():
    formatter = subject.CustomHelpFormatter("test")
    assert isinstance(formatter, argparse.HelpFormatter)


def test_setup_logging_args():
    parser = argparse.ArgumentParser()
    subject._setup_logging_args("test_module", parser)
    args = parser.parse_args([])
    assert hasattr(args, "log_level")
    assert args.log_level == "WARNING"


def test_get_argparse_type_simple():
    result_type, result_nargs = subject._get_argparse_type(str)
    assert result_type == str
    assert result_nargs is None

    result_type, result_nargs = subject._get_argparse_type(int)
    assert result_type == int
    assert result_nargs is None


def test_get_argparse_type_list():
    result_type, result_nargs = subject._get_argparse_type(list[str])
    assert result_type == str
    assert result_nargs == "*"

    result_type, result_nargs = subject._get_argparse_type(list[int])
    assert result_type == int
    assert result_nargs == "*"


def test_get_argparse_type_optional():
    result_type, result_nargs = subject._get_argparse_type(str | None)
    assert result_type == str
    assert result_nargs is None


def test_get_argparse_type_empty():
    result_type, result_nargs = subject._get_argparse_type(inspect.Parameter.empty)
    assert result_type is None
    assert result_nargs is None


def test_get_argparse_type_unsupported():
    # Test unsupported type annotations default to str
    result_type, result_nargs = subject._get_argparse_type(dict[str, int])
    assert result_type == str
    assert result_nargs is None


def test_arg_defaults_and_types_list_str():
    def main(files: list[str], flag: bool = False):
        pass

    parser = argparse.ArgumentParser()
    parser.add_argument("--flag", action="store_true")
    parser.add_argument("files", nargs="*")
    subject._setup_arg_defaults_and_types(parser, main)
    args = parser.parse_args(["file1.txt", "file2.txt"])

    assert args.files == ["file1.txt", "file2.txt"]
    assert not args.flag


def test_arg_defaults_and_types_list_int():
    def main(numbers: list[int], flag: bool = False):
        pass

    parser = argparse.ArgumentParser()
    parser.add_argument("--flag", action="store_true")
    parser.add_argument("numbers", nargs="*")
    subject._setup_arg_defaults_and_types(parser, main)
    args = parser.parse_args(["--flag", "1", "2", "3"])

    assert args.numbers == [1, 2, 3]
    assert args.flag


def test_arg_defaults_and_types_list_str_add_options():
    def main(files: list[str], flag: bool = False):
        pass

    parser = argparse.ArgumentParser()
    subject._setup_arg_defaults_and_types(parser, main, add_options=True)
    args = parser.parse_args(["file1.txt", "file2.txt"])

    assert args.files == ["file1.txt", "file2.txt"]
    assert not args.flag


def test_arg_defaults_and_types_list_int_add_options():
    def main(numbers: list[int], flag: bool = False):
        pass

    parser = argparse.ArgumentParser()
    subject._setup_arg_defaults_and_types(parser, main, add_options=True)
    args = parser.parse_args(["--flag", "1", "2", "3"])

    assert args.numbers == [1, 2, 3]
    assert args.flag


def test_varargs():
    def main(*args: str):
        pass

    parser = argparse.ArgumentParser()
    subject._setup_arg_defaults_and_types(parser, main, add_options=True)
    args = parser.parse_args(["a", "b", "c"])

    assert hasattr(args, "args")
    assert args.args == ["a", "b", "c"]


def test_optional_arg():
    def main(name: str | None = None):
        pass

    parser = argparse.ArgumentParser()
    subject._setup_arg_defaults_and_types(parser, main, add_options=True)

    args = parser.parse_args([])
    assert args.name is None

    args = parser.parse_args(["--name", "test"])
    assert args.name == "test"


def test_multiple_type_args():
    def main(files: list[str] | None = None, nums: list[int] | None = None):
        pass

    parser = argparse.ArgumentParser()
    subject._setup_arg_defaults_and_types(parser, main, add_options=True)

    args = parser.parse_args(["--files", "a.txt", "b.txt", "--nums", "1", "2"])
    assert args.files == ["a.txt", "b.txt"]
    assert args.nums == [1, 2]


def test_positional_and_optional():
    def main(pos1: str, pos2: int, *args: str, opt1: str = "default"):
        pass

    parser = argparse.ArgumentParser()
    subject._setup_arg_defaults_and_types(parser, main, add_options=True)

    args = parser.parse_args(["foo", "42", "extra1", "extra2", "--opt1", "test"])
    assert args.pos1 == "foo"
    assert args.pos2 == 42
    assert args.args == ["extra1", "extra2"]
    assert args.opt1 == "test"
