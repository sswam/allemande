#!/bin/bash

# [options] [source.ext1 target.ext2] [reference files ...]
# Translates content from one format to another

translate() {
	local style= s=1	# refer to hello.<ext> for style
	local prompt= p=	# extra prompt
	local model= m=	# model
	local edit= e=0	# edit
	local strict= S=0	# strict mode, no commentary!
	local stdio= i=0	# use stdio, not source and target files

	eval "$(ally)"

	local source target
	local from_to_prompt=""

	# if stdio option, make a temp dir with file: input output
	if [ "$stdio" -eq 1 ]; then
		local temp_dir=$(mktemp -d)
		if [ -z "$temp_dir" ]; then
			die "Failed to create temp dir"
		fi
		source="$temp_dir/input"
		target="$temp_dir/output"
		cat > "$source"
	else
		if [ "$#" -lt 2 ]; then
			usage
		fi
		source="$1"
		target="$2"
		from_to_prompt=" \`$source\` to \`$target\`"
		shift 2
	fi

	local refs=("$@")

	# Prepare the prompt
	local strict_prompt=""
	if [ "$strict" -eq 1 ]; then
		strict_prompt=", with no prelude, commentary or header, just the translation"
	fi
	prompt="Please translate$from_to_prompt as exactly as possible$strict_prompt: $prompt"

	# Call create to perform the translation
	create -q -s="$style" -m="$model" -e="$edit" "$target" "$prompt" "$source" "${refs[@]}"

	# if stdio option, cat the output
	if [ "$stdio" -eq 1 ]; then
		cat "$target"
		rm -r "$temp_dir"
	fi
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	translate "$@"
fi

# version: 0.1.2
