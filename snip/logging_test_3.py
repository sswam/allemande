#!/usr/bin/env python

import logging
from argh import arg, dispatch_command

@arg('--debug', action='store_const', dest='log_level', store=logging.DEBUG, help='Set logging level to DEBUG')
@arg('--verbose', action='store_const', dest='log_level', store=logging.INFO, help='Set logging level to INFO')
@arg('--quiet', action='store_const', dest='log_level', store=logging.ERROR, help='Set logging level to ERROR')
def main(log_level=logging.WARNING):
    """
    Main function to demonstrate different logging levels.
    """
    logging.basicConfig(level=log_level, format='%(levelname)s: %(message)s')

    print(log_level)

    logging.debug("Debug message")
    logging.info("Info message")
    logging.warning("Warning message")
    logging.error("Error message")

if __name__ == '__main__':
    dispatch_command(main)
