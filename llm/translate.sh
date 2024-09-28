#!/bin/bash

# [target.ext1] [source.ext2] [reference files ...]
# Translates content from one format to another

translate() {
	local s=1	# refer to hello.<ext> for style
	local p=	# extra prompt
	local m=	# model
	local E=0	# do not edit

	. opts

	# strict mode
	local old_opts=$(set +o)
	set -e -u -o pipefail

	local target=$1
	local source=$2
	shift 2
	local refs=("$@")

	# Prepare the prompt
	local prompt="Please translate $source to $target as exactly as possible. $p"

	# Call create.sh to perform the translation
	create.sh -s="$s" -m="$m" -E="$E" "$target" "$prompt" "$source" "${refs[@]}"

	# restore caller options
	eval "$old_opts"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	translate "$@"
fi

# version: 0.1.2
