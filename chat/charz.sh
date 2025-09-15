#!/usr/bin/env bash

# [search query]
# Show characters from ~/characters.bb by search query, one heading per query

charz() {
	eval "$(ally)"

	for query; do
		query=${query,,}
		printf "## %s\n\n" "$query"
		grep -i -e "\<$query" -e "^### " -e '^$' -- ~/characters.bb
		echo
	done |
	grep -B2 -A1 -e '^## ' -e '^- ' --no-group-separator
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	charz "$@"
fi

# version: 0.1.1
