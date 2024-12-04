#!/usr/bin/env bash

# Name something

name_main() {
	proc -m="$model" "Generate a short name to describe this:"
}

name_input() {
	# If content is not provided as an argument, read from file or stdin
	if [ -n "$content" -a -n "$file" ]; then
		usage "Content was provided as an argument and in a file"
	fi
	if [ -n "$content" ]; then
		printf -- "%s\n" "$content" | name_main
	elif [ -n "$file" ]; then
		< "$file" name_main
	else
		name_main
	fi
}

name_output() {
	# if not
	if [ "$slugify" = 0 ]; then
		name_input
	else
		local slugify_opts=()
		if [ "$lower" = 1 ]; then
			slugify_opts+=( "-l" )
		elif [ "$upper" = 1 ]; then
			slugify_opts+=( "-u" )
		elif [ "$hyphen" = 1 ]; then
			slugify_opts+=( "-H" )
		fi
		name_input | slug "${slugify_opts[@]}"
	fi
}

name() {
	local file= f=    # file to read from, defaults to stdin
	local model= m=s  # LLM model
	local slugify= s=0	# Slugify the output
	local lower= l=	# Lowercase the slug (implies slugify)
	local upper= u=	# Uppercase the slug (implies slugify)
	local hyphen= H=	# Hyphenate the slug (implies slugify)

	. opts

	# strict mode
	local old_opts=$(set +o)
	set -e -u -o pipefail
	trap 'eval "$old_opts"' RETURN

	# Support long and short options
	file=${file:-$f}
	model=${model:-$m}
	slugify=${slugify:-$s}
	lower=${lower:-$l}
	upper=${upper:-$u}
	hyphen=${hyphen:-$H}

	# non-option arguments
	local content="$*"

	# Handle output options
	name_output
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	name "$@"
fi
