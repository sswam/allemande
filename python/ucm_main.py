import argparse
import argh

import ucm

def run(func, caller_globals):
	""" Run the given function with the given options """
	parser = argparse.ArgumentParser()
	argh.add_commands(parser, [func])
	argh.set_default_command(parser, func)
	ucm.add_logging_options(parser)
	caller_globals["opts"] = parser.parse_args()
	ucm.setup_logging(caller_globals["opts"])
	argh.dispatch(parser)
