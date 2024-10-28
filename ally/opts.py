""" Command-line argument parsing """

import os
import sys
import argparse
import inspect
import logging
import sys
import warnings
from typing import Any, Callable, get_args, get_origin
import types
from io import IOBase, BufferedIOBase, BufferedReader, BufferedWriter, TextIOWrapper

from ally import meta, geput, logs

opts = sys.modules[__name__]

__version__ = "0.1.3"


def try_add_argument(parser, *args, **kwargs):
    """Add an argument to the parser if it does not already exist."""
    filtered_args = [arg for arg in args if arg not in parser._option_string_actions]
    if not filtered_args:
        raise argparse.ArgumentError(None, f"Argument already exists: {' '.join(args)}")
    parser.add_argument(*filtered_args, **kwargs)


def parse(
    main_function: Callable[..., Any],
    setup_args: Callable[[argparse.ArgumentParser], None] | None = None,
):
    """Parse command-line arguments for the main function."""
    # Get the signature of the main_function
    sig = inspect.signature(main_function)

    # Check if main_function has **kwargs
    args_name = meta.args_parameter(main_function)
    kwargs_name = meta.kwargs_parameter(main_function)

    # Check for specific parameters
    wants_get = "get" in sig.parameters
    wants_put = "put" in sig.parameters
    wants_istream = "istream" in sig.parameters
    wants_ostream = "ostream" in sig.parameters
    wants_input_source = "input_source" in sig.parameters  # ?!
    wants_text = "text" in sig.parameters
    wants_input = wants_get or wants_istream or wants_input_source
    wants_output = wants_put or wants_ostream

    # Add vars for binary I/O detection
    is_binary_input = False
    is_binary_output = False

    # Detect if istream/ostream are BufferedIOBase or descendants
    if wants_istream:
        istream_param = sig.parameters['istream']
        is_binary_input = issubclass(istream_param.annotation, BufferedIOBase)

    if wants_ostream:
        ostream_param = sig.parameters['ostream']
        is_binary_output = issubclass(ostream_param.annotation, BufferedIOBase)

    # Get the module name of the calling module
    # module_name = meta.get_module_name(2)
    module_name = meta.get_module_name(level=3)

    # Create an argument parser
    parser = argparse.ArgumentParser(formatter_class=CustomHelpFormatter, add_help=False)

    # Set up command-line arguments
    parser.description = inspect.getmodule(main_function).__doc__
    if setup_args:
        meta.call_gently(setup_args, parser=parser, arg=parser.add_argument)
    opts._setup_arg_defaults_and_types(parser, main_function)
    opts._setup_io_args(parser, wants_input=wants_input, wants_output=wants_output)
    opts._setup_logging_args(module_name, parser)
    opts._setup_help_args(module_name, parser)

    # Parse arguments, handling unknown arguments if **kwargs is present
    if args_name or kwargs_name:
        args = opts._parse_unknown_args(parser, main_function, args_name, kwargs_name)
    else:
        args = parser.parse_args()

    # open files, maybe doesn't belong here
    opts._open_files(args, parser, is_binary_input, is_binary_output)

    # setup logging based on parsed arguments, maybe doesn't belong here
    logs.set_log_level(args.log_level, root=True)
    logs.set_log_level(args.log_level, name=module_name)

    put = None

    # setup get/put functions if needed
    if wants_get and not hasattr(args, "get"):
        args.get = geput.get_istream(args.istream)
    if wants_put and not hasattr(args, "put"):
        put = args.put = geput.put_ostream(args.ostream)
    if wants_input_source and not hasattr(args, "input_source"):
        args.input_source = args.istream
    if wants_text and not hasattr(args, "text"):
        args.text = args.istream.read()
    kwargs = vars(args)

    kwargs["args"] = kwargs["opts"] = args

    optional = ["log_level", "args", "opts", "istream", "ostream", "append"]

    # remove optional args the main_function doesn't accept
    if not kwargs_name:
        kwargs = {
            k: v
            for k, v in kwargs.items()
            if k not in optional or k in sig.parameters
        }

    # extract positional args if the names match
    positional_names = [
        p.name
        for p in inspect.signature(main_function).parameters.values()
        if p.default == inspect.Parameter.empty and p.name not in (args_name, kwargs_name)
    ]

    # pass positional args in the order they are defined in the main function
    positional_args = [
        kwargs.pop(name) for name in positional_names if name in kwargs
    ]

    # add positional args for the *args parameter, if present
    if args_name:
        positional_args += kwargs.pop(args_name, [])

    return positional_args, kwargs, put


def _setup_arg_defaults_and_types(
    parser: argparse.ArgumentParser,
    main_function: Callable[..., Any],
    add_options: bool = False
) -> None:
    """
    Synchronize the parser's arguments with the parameters of the main function.

    Updates existing arguments in the parser to match the `main_function`'s
    parameter defaults and types. Optionally adds new arguments based on
    parameters not already in the parser.

    Args:
        parser (argparse.ArgumentParser): The argument parser to update.
        main_function (Callable): The main function whose parameters will be used.
        add_options (bool): If True, adds new options for parameters not in the parser.
    """
    sig = inspect.signature(main_function)
    params = sig.parameters

    # Create a set to keep track of handled parameters
    handled_params = set()

    # Update existing arguments
    for action in parser._actions:  # Note: Private attribute
        if action.dest in params:
            param = params[action.dest]
            handled_params.add(action.dest)

            # Update type if annotation is provided
            argparse_type = opts._get_argparse_type(param.annotation)
            if argparse_type:
                action.type = argparse_type

            # Update default if provided
            if param.default != inspect.Parameter.empty:
                action.default = param.default
                action.required = False

    # Add new options if requested
    if add_options:
        for name, param in params.items():
            if name in handled_params:
                continue

            if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                warnings.warn(f"Variadic parameter '{name}' is not supported by argparse.")
                continue

            kwargs = {}
            argparse_type = _get_argparse_type(param.annotation)
            if argparse_type:
                kwargs['type'] = argparse_type

            if param.default != inspect.Parameter.empty:
                kwargs['default'] = param.default
                is_positional = False
            else:
                is_positional = True

            # Determine if it should be a positional argument or an option
            if is_positional and param.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD):
                parser.add_argument(name, **kwargs)
            else:
                option_name = f'--{name.replace("_", "-")}'
                kwargs['required'] = param.default == inspect.Parameter.empty
                parser.add_argument(option_name, dest=name, **kwargs)


def _get_argparse_type(annotation):
    if annotation == inspect.Parameter.empty:
        return None
    origin = get_origin(annotation)
    args = get_args(annotation)
    if isinstance(annotation, type):
        return annotation
    elif origin is list:
        # Handle List types
        elem_type = args[0] if args else str
        def parse_list(s):
            return [elem_type(item) for item in s.split(',')]
        return parse_list
    elif origin is types.UnionType and type(None) in args:
        # Handle Optional types
        non_none_types = [arg for arg in args if arg is not type(None)]
        return non_none_types[0] if non_none_types else str
    else:
        # Default to str with a warning
        logger = logs.get_logger()
        logger.debug(f"Warning: Unsupported annotation {annotation} or {origin!r}, defaulting to str.")
        return str


def _parse_unknown_args(parser, main_function, args_name: str | None, kwargs_name: str | None):
    """
    Parse unknown arguments using parse_known_args().
    This function is used when the main function has *args or **kwargs.
    """
    # If main_function has **kwargs, use parse_known_args()
    known_args, unknown_args = parser.parse_known_args()

    kwargs = {}
    positional_args = []

    i = 0
    while i < len(unknown_args):
        arg = unknown_args[i]

        if arg == '--':
            # Treat everything after '--' as positional arguments
            positional_args.extend(unknown_args[i + 1:])
            break
        elif arg.startswith('--'):
            # Handle long options
            key = arg.lstrip('-')
            if '=' in key:
                # Format: --key=value
                key, value = key.split('=', 1)
            else:
                # Format: --key value
                if i + 1 < len(unknown_args) and not unknown_args[i + 1].startswith('-'):
                    value = unknown_args[i + 1]
                    i += 1
                else:
                    # Options without values are considered as flags with value True
                    value = True
            kwargs[key] = value
        elif arg.startswith('-') and len(arg) > 1:
            # Handle short options
            key = arg.lstrip('-')
            if i + 1 < len(unknown_args) and not unknown_args[i + 1].startswith('-'):
                value = unknown_args[i + 1]
                i += 1
            else:
                # Options without values are considered as flags with value True
                value = True
            kwargs[key] = value
        else:
            # Positional argument
            positional_args.append(arg)

            # Positional argument; these must be declared
            raise ValueError(f"Unknown argument: {arg}")

        i += 1

    # Check for unknown arguments
    if positional_args and not has_args:
        raise ValueError(f"Unknown arguments: {positional_args}")
    if kwargs and not has_kwargs:
        raise ValueError(f"Unknown options: {kwargs.keys()}")

    # Combine known and unknown arguments
    args = argparse.Namespace(**vars(known_args), **kwargs)

    # Add positional arguments if any
    if positional_args:
        args.positional_args = positional_args

    return args


def _setup_io_args(parser: argparse.ArgumentParser, wants_input=True, wants_output=True):
    """Set up command-line argument parsing for input/output options."""
    if wants_input:
        try_add_argument(
            parser,
            "-i",
            "--in",
            "--input",
            dest="istream",
            type=argparse.FileType("r"),
            default=sys.stdin,
            help="input file",
        )
    if wants_output:
        try_add_argument(
            parser,
            "-o",
            "--out",
            "--output",
            dest="ostream",
            type=argparse.FileType("w"),
            default=sys.stdout,
            help="output file",
        )
        try_add_argument(
            parser,
            "-a",
            "--append",
            action="store_true",
            help="append to output file",
        )


def _setup_logging_args(module_name: str, parser: argparse.ArgumentParser):
    """Set up command-line argument parsing for logging options."""

    # Get the log_level from {SCRIPT_NAME}_LOG_LEVEL, or WARNING.
    log_level_var_name = f"{module_name.upper()}_LOG_LEVEL"
    default_log_level = os.environ.get(log_level_var_name, "WARNING")

    try_add_argument(
        parser,
        "-l",
        "--log-level",
        default=default_log_level,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level {DEBUG,INFO,WARNING,ERROR,CRITICAL}",
    )
    try_add_argument(
        parser,
        "-d",
        "--debug",
        action="store_const",
        const="DEBUG",
        dest="log_level",
        help="Set logging level to DEBUG",
    )
    try_add_argument(
        parser,
        "-q",
        "--quiet",
        action="store_const",
        const="ERROR",
        dest="log_level",
        help="Set logging level to ERROR",
    )
    try_add_argument(
        parser,
        "-v",
        "--verbose",
        action="store_const",
        const="INFO",
        dest="log_level",
        help="Set logging level to INFO",
    )


def _setup_help_args(module_name: str, parser: argparse.ArgumentParser):
    try_add_argument(parser, '-h', '--help', action='help', default=argparse.SUPPRESS, help="show this help message and exit")


def _open_files(args: argparse.Namespace, parser: argparse.ArgumentParser, is_binary_input: bool, is_binary_output: bool):
    """Open input/output files if specified in the arguments."""
    no_clobber = getattr(args, "no_clobber", False)
    append = getattr(args, "append", False)

    def process_stream_arg(arg_name, mode, binary, append=False, no_clobber=False):
        arg_value = getattr(args, arg_name, None)
        if isinstance(arg_value, TextIOWrapper):
            if mode == "r" and is_binary_input:
                binary_reader = BufferedReader(arg_value.buffer)
                setattr(args, arg_name, binary_reader)
            elif mode in ["w", "a"] and is_binary_output:
                binary_writer = BufferedWriter(arg_value.buffer)
                setattr(args, arg_name, binary_writer)
            return
        if not isinstance(arg_value, str):
            return
        if mode == "w":
            main_mode = "a" if append else "x" if no_clobber else "w"
            binary_mode = "b" if binary else ""
            mode = main_mode + binary_mode
            file_obj = open(arg_value, mode)
            print(f"Opening {arg_name} file: {arg_value!r} with mode: {mode!r}")
        elif mode == "r":
            file_obj = open(arg_value, mode)
        setattr(args, arg_name, file_obj)

    process_stream_arg("istream", mode="r", binary=is_binary_input)
    process_stream_arg("ostream", mode="w", binary=is_binary_output, append=append, no_clobber=no_clobber)


class CustomHelpFormatter(
    argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter
):
    """
    - show repr for default values
    - don't show defaults if the defaults is None
    - show .name not repr for stdin and stdout
    - show class name for other IOBase objects
    """

    def __init__(self, *args, **kwargs):
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

