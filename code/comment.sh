#!/bin/bash

# [file] ["extra prompt"]
# Add comments to code, either streaming or modifying a file in-place

comment() {
	local m=    # LLM model
	local E=0   # do not edit

	eval "$(<$(W ally))"

	local file=${1:--}
	shift || true
	local extra_prompt=$*
	local prompt="Please add comments for chunks of code, describing how it works. Not too many. Preferably on separate lines. DO NOT CHANGE THE CODE ITSELF please. Do not remove docstring comments, but you can correct them. If the code is a whole program, add or correct a header comment describing what it does if needed, including each CLI option if any, and examples of usage covering common options at least. Code must be in \`\`\`s. Use appropiate comment standards such as PyDoc for the language. $extra_prompt"
	code_modify -E="$E" "$file" process -m="$m" "$prompt"
}

# Run the comment function if the script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
	comment "$@"
fi
