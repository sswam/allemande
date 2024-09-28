#!/bin/bash

# [input files] [custom prompt]
# Combines similar inputs to get the best results

combine() {
	local model= m=	# LLM model
	local extra_prompt= p=	# Custom prompt

	. opts

	# Support long and short options
	model=${model:-$m}
	extra_prompt=${extra_prompt:-$p}

	# strict mode
	local old_opts=$(set +o)
	set -e -u -o pipefail

	# Collect input files
	local input_files=("$@")

	local prompt="Combine the following inputs to create \
		a comprehensive and coherent result. $extra_prompt"

	cat_named.py "${input_files[@]}" |
	process -m="$model" "$prompt"

	# restore caller options
	eval "$old_opts"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	combine "$@"
fi
