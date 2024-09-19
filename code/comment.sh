#!/bin/bash -eu
# [file] ["extra prompt"]
# Add comments to code, either streaming or modifying a file in-place

# Source the ally bash library
. ally.sh

comment() {
	local m=	# LLM model

	. opts

	local file=${1-}
	shift
	local extra_prompt=$*
	local prompt="Please add comments for chunks of code, describing how it works. Not too many. DO NOT CHANGE THE CODE ITSELF please. Do not remove docstring comments, but you can correct them. $extra_prompt"

	# If no file is provided, process input stream

	code_modify "$file" process -m="$m" "$prompt"
}

# Run the comment function if the script is executed directly
if [ "$BASH_SOURCE" = "$0" ]; then
	comment "$@"
fi
