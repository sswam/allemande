#!/usr/bin/env bash

# [search query]
# Show LoRAs from ~/lora.bb by search query, one heading per query

loraz() {
	local nlimit= n=20      # limit number of results per query

	eval "$(ally)"

	for query; do
		query=${query,,}
		printf "## %s\n" "$query"
		grep -i -e "$query" -e "^| <lora:name:weight>" -e '^|--|' -- ~/lora.bb
		echo
	done
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	loraz "$@"
fi

# version: 0.1.1
