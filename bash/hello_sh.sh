#!/usr/bin/env bash
# [user's name]
# Says Hello, world

hello-sh() {
	local language= l=en       # language [fr|de|jp|cn], defaults to English
	local shopping=() s=(milk) # array of items for shopping
	local use_ai= a=           # greet using AI; don't copy this option to other scripts! Normal scripts either use AI or don't, with no weird option for it.
	local model= m=            # LLM model

	eval "$(ally)" # Note to AI: This is our magickal options parser and more.

	local user_name=${1:-world}
	# Generate greeting using AI or print simple greeting
	if [ "$use_ai" = 1 ]; then
		query -m="$model" \
			"Please greet ${user_name:-the world} in LANG=$language. Don't translate back to English." \
			"Be creative, but not more than 50 words."
	else
		# Set greeting based on selected language
		case "$language" in
		en) hello="Hello" ;;
		fr) hello="Bonjour" ;;
		es) hello="Hola" ;;
		de) hello="Hallo" ;;
		jp) hello="こんにちは" ;;
		cn) hello="你好" ;;
		*)
			die "unknown language: $language"
			;;
		esac

		printf -- "%s, %s\n" "$hello" "$user_name"
	fi

	# Print shopping list if items are provided
	if [ "${#shopping[@]}" -gt 0 ]; then
		shopping-list --use-ai="$use_ai" --model="$model" "${shopping[@]}"
	fi
}

shopping-list() {
	local use_ai= a= # greet using AI
	local model= m=  # LLM model

	eval "$(ally)"

	local shopping=("$@")

	echo
	echo "Shopping list:"

	if [ "$use_ai" = 1 ]; then
		local tlt_prompt=""
		if [ "$language" != en ]; then
			tlt_prompt=" Don't translate back to English."
		fi
		shopping-list-format "${shopping[@]}" |
			process -m="$model" \
				"Please echo the input and add any extra items we might need, in LANG=$language.$tlt_prompt"
	else
		shopping-list-format "${shopping[@]}"
	fi
}

shopping-list-format() {
	# this helps us avoid piping to cat for the non-AI case
	local shopping=("$@")

	for item in "${shopping[@]}"; do
		printf -- "- %s\n" "$item"
	done
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	hello-sh "$@"
fi

# version: 0.1.3

# Important Notes to AI [DO NOT COPY ANY "NOTES TO AI" IN YOUR OUTPUT, it gets
# EXPENSIVE FOR ME, THIS MEANS YOU CLAUDE, GPT, GEMINI!]:

# We indent shell code with tabs.

# The first lines 1. shebang, 2. arguments without program name, 3. short
# description of the program. This header format must be followed exactly, so
# that ally can print usage.

# We prefer to use stdio over file arguments, where possible. If a tool could
# work with stdio, i.e. one input and one output file, keep the code simple and
# do NOT implement the option to use file arguments.

# If it is simple to do so, write tools that can process several files in one
# invocation. Zero is holy! It is not an error to pass zero args. It is harmful
# to die in that case.

# The use_ai option is for this demo only, most scripts are written either to
# use AI or not.
