#!/usr/bin/env bash

# [URL]
# Generates a short filename for documenting a resource

name_url() {
	local url=$1
	local model= m=s

	. opts

	# Support long and short options
	model=${model:-$m}

	[ -n "$url" ] || usage "URL is required"

	que -m="$model" "What's a short filename to document this resource, lower-case with .md extension: $url"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	name_url "$@"
fi
