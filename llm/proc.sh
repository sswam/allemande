#!/usr/bin/env bash

# [prompt [attachment...]]
# Process input text with an LLM, for a concise answer

proc() {
	local model= m=     # LLM model
	local empty_ok= e=  # empty input is okay
	local system= s=    # system prompt

	eval "$(ally)"

	local prompt="${1:-}"
	shift || true

	local refs=("$@")

	opts=()
	if [ "$empty_ok" = 1 ]; then
		opts+=("--empty-ok")
	fi
	if [ -n "$system" ]; then
		opts+=("--system=$system")
	fi

	prompt="$prompt Please reply as concise as possible, with no boilerplate \
or explanation. Do not abbreviate text unrelated to the request. \
If editing, do not make edits that are not requested (e.g. removing comments \
or blank lines). If the input has code but does not include code quoting with \
\`\`\`, the output should not include \`\`\` either. If writing code, be \
concise but clear, not obscure. No intro or concluding text. Thanks\!"

	process -m="$model" "${opts[@]}" "$prompt" "${refs[@]}" | text-strip
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	proc "$@"
fi

# version: 1.0.4
