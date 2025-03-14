#!/usr/bin/env bash
# [file or path]
# Shows git history with patches

git-show-history-main() {
	git log --color="$color" --oneline --patch -- "$@"
}

git-show-history() {
	local color= c=auto    # colorize output [auto|never|always]

	eval "$(ally)"

	# Pass the color option to git commands
	if [ -t 1 ]; then
		color=always
		git-show-history-main "$@" | less -R
	else
		git-show-history-main "$@"
	fi
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	git-show-history "$@"
fi

# version: 0.1.0
