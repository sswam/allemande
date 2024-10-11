""" Deprecated functions. """

import os
import sys
import argparse
from io import IOBase, TextIOWrapper
from io import StringIO
from typing import Callable, TextIO
import argh
import traceback

from ally import main, meta, opts, logs, geput

old = sys.modules[__name__]


def run(commands: Callable | list[Callable], warn_deprecated=True) -> None:
    """
    Set up logging, parse arguments, and run the specified command(s).

    Args:
        commands (Callable|list[Callable]]): The command function(s) to be executed.

    Raises:
        Exception: Any exception that occurs during command execution.
    """
    if warn_deprecated:
        meta.deprecated("old.run", "main.go")

    module_name = meta.get_module_name(2)

    parser = argh.ArghParser(
        formatter_class=lambda prog: old.CustomHelpFormatter(
            prog, max_help_position=40,
            warn_deprecated=False,
        ),
        allow_abbrev=False,
    )

    if isinstance(commands, list):
        commands = [meta.async_to_sync_wrapper(fn) for fn in commands]
        argh.add_commands(parser, commands)
    else:
        commands = meta.async_to_sync_wrapper(commands)
        argh.set_default_command(parser, commands)

    opts._setup_logging_args(module_name, parser)

    # fix IO args to be strings, and display nicely in help message
    old._fix_io_arguments(parser)

    # Parse arguments without dispatching
    args = parser.parse_args()

    # Open files
    opts._open_files(args, parser)

    # Setup logging based on parsed arguments
    logs.setup_logging(module_name, args.log_level)

    # dispatch, and show errors nicely
    try:
        if isinstance(commands, list):
            argh.dispatch(parser)
        else:
            argh.dispatching.run_endpoint_function(commands, args)
    except Exception as e:
        logger = logs.get_logger(1)
        logger.error(f"Error: %s %s", type(e).__name__, str(e))
        tb = traceback.format_exc()
        logger.debug("Full traceback:\n%s", tb)


class CustomHelpFormatter(
    argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter
):
    """
    - show repr for default values
    - don't show defaults if the defaults is None
    - show .name not repr for stdin and stdout
    - show class name for other IOBase objects
    """

    def __init__(self, *args, warn_deprecated=True, **kwargs):
        if warn_deprecated:
            meta.deprecated("old.CustomHelpFormatter", "main.go")
        super().__init__(*args, **kwargs)

    def _expand_help(self, action):
        """
        Based on ArgumentDefaultsHelpFormatter
        with refernce to argh.constants.CustomFormatter
        """
        params = dict(vars(action), prog=self._prog)
        for name in list(params):
            if params[name] is argparse.SUPPRESS:
                del params[name]
        for name in list(params):
            if hasattr(params[name], "__name__"):
                params[name] = params[name].__name__
        if params.get("choices") is not None:
            choices_str = ", ".join([str(c) for c in params["choices"]])
            params["choices"] = choices_str

        if "default" in params:
            if params["default"] in [None, False]:
                action.default = argparse.SUPPRESS
            elif isinstance(params["default"], IOBase):
                if hasattr(params["default"], "name"):
                    params["default"] = params["default"].name
                else:
                    params["default"] = f"<{params['default'].__class__.__name__}>"
            else:
                params["default"] = repr(params["default"])

        string = self._get_help_string(action) % params
        return string

    def _format_args(self, action, default_metavar):
        if action.dest in ["istream", "ostream"]:
            return "FILE"
        return super()._format_args(action, default_metavar)


def _fix_io_arguments(parser: argparse.ArgumentParser):
    for arg in ["--istream", "--ostream"]:
        if arg in parser._option_string_actions:
            action = parser._option_string_actions[arg]
            if action.default == sys.stdin:
                action.help = "input file"
            elif action.default == sys.stdout:
                action.help = "stdout"
            action.type = str


def io(
    istream: TextIO = sys.stdin, ostream: TextIO = sys.stdout, warn_deprecated=True
) -> tuple[Callable[[], str], Callable[[str], None]]:
    """
    Create input and output functions for handling I/O operations.

    Args:
        istream (TextIO, optional): istream stream. Defaults to sys.stdin.
        ostream (TextIO, optional): Output stream. Defaults to sys.stdout.

    Returns:
        tuple[Callable, Callable]: A tuple of get and put functions.
    """
    if warn_deprecated:
        meta.deprecated("old.io", "main.go")

    return geput.setup_get(istream), geput.setup_put(ostream)


class TextInput:
    """
    A text input manager that can read from files, stdin, or StringIO.
    """
    def __init__(
        self,
        file=None,
        mode="r",
        encoding="utf-8",
        errors="strict",
        newline=None,
        search=False,
        basename=False,
        stdin_name=None,
        warn_deprecated=True,
    ):
        if warn_deprecated:
            meta.deprecated("main.io", "main.go")

        stdin_name = stdin_name or "input"

        if mode not in ("r", "rb", "rt"):
            raise ValueError("Mode must be 'r', 'rb', or 'rt'")

        self.encoding = encoding
        self.errors = errors
        self.newline = newline

        if file in (None, "-", sys.stdin):
            self.display = stdin_name
            self.file = sys.stdin
        elif isinstance(file, str):
            if search and not os.path.exists(file):
                file = find_in_path(file)
            self.display = os.path.basename(file) if basename else file
            self.file = open(
                file, mode, encoding=encoding, errors=errors, newline=newline
            )
        elif isinstance(file, StringIO):
            self.display = "StringIO"
            self.file = file
        else:
            self.display = getattr(file, "name", "file-like object")
            self.file = file

        if not isinstance(self.file, TextIOWrapper) and hasattr(self.file, "read"):
            self.file = TextIOWrapper(
                self.file, encoding=encoding, errors=errors, newline=newline
            )

    def read(self, size=-1):
        return self.file.read(size)

    def readline(self, size=-1):
        return self.file.readline(size)

    def readlines(self, hint=-1):
        return self.file.readlines(hint)

    def __iter__(self):
        return iter(self.file)

    def close(self):
        if self.file is not sys.stdin:
            self.file.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def load(path: str, comments=False, blanks=False) -> list[str]:
    """Load a list of strings from a file"""
    with open(resource(path), "r", encoding="utf-8") as f:
        return [
            line
            for line in f.read().splitlines()
            if (blanks or line) and (comments or not line.startswith("#"))
        ]
