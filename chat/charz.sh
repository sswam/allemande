#!/usr/bin/env bash

# [search query]
# Show characters from ~/characters.bb by search query, one heading per query

charz() {
	eval "$(ally)"

	for query; do
		# Check if original query contains any uppercase letters
		local grep_option
		if [[ "$query" = "${query,,}" ]]; then
			grep_option="-i"
		else
			grep_option=""
		fi

		printf "## %s\n\n" "$query"
		grep $grep_option -e "\<$query" -e "^### " -e '^$' -- ~/characters.bb
		echo
	done |
	grep -B2 -A1 -e '^## ' -e '^- ' --no-group-separator
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	charz "$@"
fi

# version: 0.1.1
