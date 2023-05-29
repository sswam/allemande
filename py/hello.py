#!/usr/bin/env python3
""" hello.py:	 """

import sys
import os
import logging
import argh

logger = logging.getLogger(__name__)

def hello(name="world", greeting="Hello", template="%(greeting)s, %(name)s"):
	""" Say hello to name """
	return(template % locals())

if __name__ == "__main__":
	argh.dispatch_command(hello)
