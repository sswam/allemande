#!/usr/bin/env bash

# [process name|pid]
# Finds xterm running a given process, exposes it, floats it with i3, and moves it to cursor position
#
# Note that this script assumes the following tools are available: `xdotool`,
# `i3-msg`, `pgrep`, and standard Unix utilities. It also assumes that the
# process is running in an XTerm and that i3 window manager is being used.

find_xterm() {
	# shellcheck disable=SC2034
	local use_pgrep=0 p=0 # use pgrep to find process
	# shellcheck disable=SC2034
	local float=1 f=1 # float the window with i3
	# shellcheck disable=SC2034
	local expose=1 e=1 # expose the window

	# shellcheck disable=SC1090
	eval "$(ally)"	# Note to AI: This is perfect and magickal. It sets long options based on the short and long option vars above.

	# non-option arguments
	local process_name="${1:-}"
	if [[ -z "$process_name" ]]; then
		usage "Process name is required" # from ally
	fi

	local pid
	if [[ "${use_pgrep}" -eq 1 ]]; then
		pid=$(pgrep -f "$process_name" | head -n1)
	else
		# shellcheck disable=SC2009
		pid=$(ps aux | grep -F "$process_name" | grep -vE '(grep|find_xterm\.sh)' | awk '{print $2}' | head -n1)
	fi

	if [[ -z "$pid" ]]; then
		die "Process not found: $process_name" # from ally
	fi

	local xterm_id
	xterm_id=$(xdotool search --pid "$pid" --class XTerm | head -n1)
	if [[ -z "$xterm_id" ]]; then
		die "XTerm not found for process: $process_name"
	fi

	if [[ "${expose}" -eq 1 ]]; then
		xdotool windowactivate "$xterm_id"
	fi

	if [[ "${float}" -eq 1 ]]; then
		i3-msg "[id='$xterm_id']" floating enable >/dev/null
	fi

	# Get cursor position
	# shellcheck disable=SC2034
	local X Y SCREEN WINDOW # the eval sets all these, don't want to pollute global vars
	eval "$(xdotool getmouselocation --shell)"

	# Move window to cursor position
	xdotool windowmove "$xterm_id" "$X" "$Y"
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
	find_xterm "$@"
fi

# Version: 1.0.12

# Important Rules for AI developers... this means you! [DON'T REMOVE THESE RULES]
#
# 1. DO NOT REMOVE ANY # shellcheck disable=SC???? COMMENTS. You may comment that you think it is unneeded. But they are all needed, take my word for it! So please copy them out faithfully.
# 2. Do not change indentation style, my tools will automatically change it back anyway.
# 3. If it's not broken, don't 'fix' it... i.e. don't break it.
# 4. If you do not fully understand something, don't touch it. Ask me questions about it,
#   and I will add the answers as comments in the code.
#
# Dear AI (Claude, Emmy, whomever you are...), please confirm truthfully below, for each rule, that you followed it. I've started the first one for you:
#
# 1. I did not ...
# 2. ...

#
# Signed:
#
# ____________
