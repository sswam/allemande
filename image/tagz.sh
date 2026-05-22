#!/usr/bin/env bash

# [tag search query]
# Show tags from ~/danbooru_tags_post_count.csv by search query, one heading per query

tagz() {
	local nlimit= n=20      # limit number of results per tag
	local markdown= m=1     # output markdown

	eval "$(ally)"

	for query; do
		query=${query,,}
		query=${query%,}
		printf "## %s\n" "$query"
		(
			techo count tag
			grep -i -- "\(\\<\|_\)$query.*," ~/danbooru_tags_post_count.csv | sed 's/_/ /g; s/,/\t/;' | kut 2 1 | head -n "$nlimit" || true
		) |
		if (( markdown )); then
 		        tsv2markdown
		else
			cat
		fi
		echo
	done
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	tagz "$@"
fi

# version: 0.1.1
