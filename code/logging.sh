#!/usr/bin/env bash
# [file] ["extra prompt"]
# Add logging to code, either streaming or modifying a file in-place

logging() {
	local model= m=     # LLM model
	local no_edit= E=0  # do not open in an editor

	eval "$(ally)"

	local file=${1:--}
	shift || true
	local extra_prompt=$*
	local prompt="Please add logging statements to the code, at info level unless specified otherwise. Add for key operations, not excessively. Code must be in \`\`\`s. $extra_prompt"
	code_modify -E="$no_edit" "$file" process -m="$model" "$prompt"
}

# Run the add_logging function if the script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
	logging "$@"
fi
