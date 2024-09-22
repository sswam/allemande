#!/bin/bash

# [template_file]
# Processes a template file using heredoc

# Version 1.0.1

process_template() {
	local d=    # debug flag
	local p=    # permissive flag
	local eval_opts=""

	. opts

	# strict mode
	local old_opts=$(set +o)
	set -e -u -o pipefail

	local template=$1

	# Set evaluation options if not in permissive mode
	if [ "$p" != 1 ]; then
		eval_opts="$eval_opts -eu -o pipefail"
	fi

	# Function to wrap the template content in a heredoc
	wrap_heredoc() {
		local template=$1
		echo "cat <<EOF"
		cat "$template"
		echo "EOF"
	}

	# If in debug mode, print the wrapped heredoc
	# Otherwise, execute the wrapped heredoc using bash
	if [ -n "$d" ]; then
		wrap_heredoc "$template"
	else
		wrap_heredoc "$template" | bash $eval_opts
	fi

	# restore caller options
	eval "$old_opts"
}

if [ "$BASH_SOURCE" = "$0" ]; then
	process_template "$@"
fi
