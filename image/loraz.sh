#!/usr/bin/env bash

# [search query]
# Show LoRAs from ~/lora.bb by search query, one heading per query

loraz() {
	nsfw= n=0  # include NSFW loras

	eval "$(ally)"

	files=("$HOME/lora.bb")
	if [ "$nsfw" = 1 ]; then
		files+=("$HOME/lora-nsfw.bb")
	elif [ "$nsfw" = 2 ]; then
		files=("$HOME/lora-nsfw.bb")
	fi

	for query; do
		query=${query,,}
		printf "## %s\n" "$query"
		cat "${files[@]}" | uniqo | grep -i -e "$query" -e "^| <lora:name:weight>" -e '^|--|'
		echo
	done
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	loraz "$@"
fi

# version: 0.1.1
