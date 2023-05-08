#!/usr/bin/env python3
""" user-set-theme.py: set the user's theme for Ally Chat """

import os
from pathlib import Path

import argh

def set_theme(user, theme):
	""" Set the user's theme for Ally Chat. """

	# create a symlink from $ALLYCHAT_HOME/static/themes/$theme.css to $ALLYCHAT_HOME/users/$user/theme.css
	home = os.environ['ALLYCHAT_HOME']
	os.chdir(home)

	target = Path("..")/".."/"static"/"themes"/(theme + ".css")
	link = Path("users")/user/"theme.css"
	link.unlink(missing_ok=True)
	link.symlink_to(target)

if __name__ == '__main__':
	argh.dispatch_command(set_theme)
