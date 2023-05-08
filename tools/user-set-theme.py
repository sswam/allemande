#!/usr/bin/env python3
""" user-set-theme.py: set the user's style sheet for Ally Chat """

import os
from pathlib import Path

import argh

def set_theme(user, theme):
	""" Set the user's style sheet for Ally Chat. """

	# create a symlink from $ALLYCHAT_HOME/static/styles/$theme.css to $ALLYCHAT_HOME/users/$user/styles.css
	home = os.environ['ALLYCHAT_HOME']
	os.chdir(home)

	target = Path("..")/".."/"static"/"styles"/(theme + ".css")
	link = Path("users")/user/"styles.css"
	link.unlink(missing_ok=True)
	link.symlink_to(target)

if __name__ == '__main__':
	argh.dispatch_command(set_theme)
