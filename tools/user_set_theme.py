#!/usr/bin/env python3
""" user-set-theme.py: set the user's theme for Ally Chat """

import os
from pathlib import Path
import random

from create_relative_symlink import create_relative_symlink

import argh

# ls webchat/static/themes | perl -ne 'print if /\.css$/ && !/^(default|template|large)\.css$/' | fortune.pl

EXCLUDE_THEMES = ["default", "template", "large"]
THEMES = Path(os.environ['ALLYCHAT_THEMES'])

def all_themes():
	return [f.stem for f in THEMES.glob("*.css") if f.stem not in EXCLUDE_THEMES]

def set_theme(user, theme=None, fortune=False):
	""" Set the user's theme for Ally Chat. """

	# create a symlink from $ALLYCHAT_HOME/static/themes/$theme.css to $ALLYCHAT_HOME/users/$user/theme.css
	home = os.environ['ALLYCHAT_HOME']
	os.chdir(home)

	if fortune:
		themes = all_themes()
		theme = random.choice(themes)

	user_theme_file = Path("users")/user/"theme.css"

	theme_css = theme if theme.endswith(".css") else theme + ".css"

	create_relative_symlink(THEMES/theme_css, user_theme_file, force=True)

if __name__ == '__main__':
	argh.dispatch_command(set_theme)
