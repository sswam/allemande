def run(commands: Callable | List[Callable]) -> None:
    """
    Set up logging, parse arguments, and run the specified command(s).

    Args:
        commands (Union[Callable, List[Callable]]): The command function(s) to be executed.

    Raises:
        Exception: Any exception that occurs during command execution.
    """
    # Get the name of the calling module
    module_name = main.get_module_name(2)

    # Create an argument parser with custom formatting
    parser = argh.ArghParser(formatter_class=lambda prog: main.CustomHelpFormatter(prog, max_help_position=40), allow_abbrev=False)

    # Handle single command or multiple commands
    if isinstance(commands, list):
        commands = [create_argh_compatible_wrapper(fn) for fn in commands]
        argh.add_commands(parser, commands)
    else:
        commands = create_argh_compatible_wrapper(commands)
        argh.set_default_command(parser, commands)

    # Set up logging arguments and fix I/O arguments
    main.setup_logging_args(module_name, parser)
    main._fix_io_arguments(parser)

    # Parse arguments, handling '--' separator if present
    try:
        split_index = sys.argv.index('--')
        args = parser.parse_args(sys.argv[1:split_index])
        arg += sys.argv[split_index + 1:]
    except ValueError:
        args = parser.parse_args()

    # Open files specified in arguments
    main._open_files(args, parser)

    # Set up logging based on parsed arguments
    main.setup_logging(module_name, args.log_level)

    # Execute the command(s)
    try:
        if isinstance(commands, list):
            argh.dispatch(parser, argv=sys.argv[1:split_index])
        else:
            argh.dispatching.run_endpoint_function(commands, args)
    except Exception as e:
        # Log any exceptions that occur during execution
        logger = main.get_logger(1)
        logger.error(f'Error: %s %s', type(e).__name__, str(e))
        tb = traceback.format_exc()
        logger.debug('Full traceback:\n%s', tb)
