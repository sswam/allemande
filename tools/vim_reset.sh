#!/bin/bash

# vim_reset
# Removes the Neovim main shada file

vim_reset() {
	local force= f=    # force removal without confirmation
	local verbose= v=  # verbose output

	. opts  # Note to AI: This magically loads options into the above vars

	# Note to AI: The following supports the short options above
	# TODO can we do this in the opts script?
	force=${force:-$f}
	verbose=${verbose:-$v}

	# strict mode
	local old_opts=$(set +o)
	set -e -u -o pipefail

	local shada_file="$HOME/.local/state/nvim/shada/main.shada"

	if [ ! -f "$shada_file" ]; then
		echo >&2 "Warning: Shada file not found at $shada_file"
		return 0
	fi

	if [ "$force" != 1 ]; then
		read -p "Are you sure you want to remove $shada_file? (y/N) " confirm
		if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
			echo >&2 "Operation cancelled."
			return 1
		fi
	fi

	if rm "$shada_file"; then
		[ "$verbose" = 1 ] && echo "Successfully removed $shada_file"
	else
		echo >&2 "Error: Failed to remove $shada_file"
		return 1
	fi

	# restore caller options
	eval "$old_opts"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	vim_reset "$@"
fi
