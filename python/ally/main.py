import logging

import argh


def setup_logging(log_level):
    print(f"setup_logging: {log_level=}")
    if log_level is None:
        return
    if log_level == logging.DEBUG:
        fmt = "%(asctime)s %(levelname)s %(name)s %(message)s"
    else:
        fmt = "%(message)s"
    logging.basicConfig(level=log_level, format=fmt)


def setup_logging_args():
    parser = argh.ArghParser()
    parser.add_argument("-d", "--debug", action="store_const", const="DEBUG", dest="log_level")
    parser.add_argument("-q", "--quiet", action="store_const", const="ERROR", dest="log_level")
    parser.add_argument("-v", "--verbose", action="store_const", const="INFO", dest="log_level")
    return parser


def run(command):
    parser = setup_logging_args()
    argh.set_default_command(parser, command)
    argh.dispatch(parser)
