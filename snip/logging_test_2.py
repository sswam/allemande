#!/usr/bin/env python

import argparse
import logging

parser = argparse.ArgumentParser()
parser.add_argument('--debug', action='store_const', dest='log_level', const=logging.DEBUG)
parser.add_argument('--verbose', action='store_const', dest='log_level', const=logging.INFO)
parser.add_argument('--quiet', action='store_const', dest='log_level', const=logging.ERROR)
parser.set_defaults(log_level=logging.WARNING)
args = parser.parse_args()

logging.basicConfig(level=args.log_level, format='%(levelname)s: %(message)s')

logging.debug("Debug message")
logging.info("Info message")
logging.warning("Warning message")

