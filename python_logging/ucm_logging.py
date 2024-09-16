import logging

def setup_logging(args):
    """ Set up logging. """

    # get basename of program in upper case
    prog_name_uc = os.path.basename(sys.argv[0]).upper()

    log_file = args.log or os.environ.get(f'{prog_name_uc}_LOG')
    fmt = "%(message)s"
    if args.log_level == logging.DEBUG:
        fmt = "%(asctime)s %(levelname)s %(name)s %(message)s"

    # if a log_file was specified, use it
    log_file = log_file or os.environ.get('CHATGPT_LOG_FILE')
    logging.basicConfig(level=args.log_level, format=fmt, filename=log_file)

def add_logging_options(parser):
    """ Add logging options to an argument parser. """
    logging_group = parser.add_argument_group('Logging options')
    logging_group.set_defaults(log_level=logging.WARNING)
    logging_group.add_argument('-d', '--debug', dest='log_level', action='store_const', const=logging.DEBUG, help="show debug messages")
    logging_group.add_argument('-v', '--verbose', dest='log_level', action='store_const', const=logging.INFO, help="show verbose messages")
    logging_group.add_argument('-q', '--quiet', dest='log_level', action='store_const', const=logging.ERROR, help="show only errors")
    logging_group.add_argument('-Q', '--silent', dest='log_level', action='store_const', const=logging.CRITICAL, help="show nothing")
    logging_group.add_argument('--log', default=None, help="log file")
