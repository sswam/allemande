#!/usr/bin/env bash

# [tag search query]
# Show tags from ~/tags by search query, one heading per query

tagz() {
	local nlimit= n=20      # limit number of results per tag

	eval "$(ally)"

	for query; do
		printf "## %s\n" "$query"
		(
			techo count tag
			grep -- "$query" ~/danbooru_tags_post_count.csv | sed 's/_/ /g; s/,/\t/;' | kut 2 1 | head -n "$nlimit" || true
		) | tsv2markdown
		echo
	done
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	tagz "$@"
fi

# version: 0.1.1
