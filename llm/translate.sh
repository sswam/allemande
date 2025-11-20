#!/bin/bash

# [options] [source.ext1 target.ext2] [reference files ...]
# OR: [options] target-description < input > output
# Translates content from one format to another

translate() {
	local style= s=1	# refer to hello.<ext> for style
	local prompt= p=	# extra prompt
	local model= m=	# model
	local edit= e=0	# edit
	local strict= S=0	# strict mode, no commentary!

	eval "$(ally)"

	if [ "$#" -lt 1 ]; then
		usage
	fi

	local source target from_to_prompt temp_dir

	# Determine mode: file-to-file vs stdin-to-description
	if [ "$#" -ge 2 ] && [ -f "$1" ]; then
		# File mode: translate source.ext1 to target.ext2
		source="$1"
		target="$2"
		from_to_prompt=" \`$source\` to \`$target\`"
		shift 2
	else
		# Stdio mode: translate to description from stdin
		local target_desc="$1"
		from_to_prompt=" to $target_desc"
		shift

		temp_dir=$(mktemp -d)
		if [ -z "$temp_dir" ]; then
			die "Failed to create temp dir"
		fi
		source="$temp_dir/input"
		target="$temp_dir/output"
		cat > "$source"
	fi

	local refs=("$@")

	# Prepare the prompt
	local strict_prompt=""
	if [ "$strict" -eq 1 ]; then
		strict_prompt=", with no prelude, commentary or header, just the translation"
	fi
	prompt="Please translate$from_to_prompt as well as you can$strict_prompt: $prompt"

	# Call create to perform the translation
	create -q -s="$style" -m="$model" -e="$edit" "$target" "$prompt" "$source" "${refs[@]}"

	# If stdio mode, output result and cleanup
	if [ -n "$temp_dir" ]; then
		cat "$target"
		rm -r "$temp_dir"
	fi
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	translate "$@"
fi

# version: 0.1.3
