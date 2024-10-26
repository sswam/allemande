#!/bin/bash -eu

# [arg ...]
# Summarizes an API compactly in markdown with expert-level details

summary-api() {
	local model= m= # LLM model

	eval "$(ally)"

	summary -m="$model" "Please summarize the API concisely in markdown. \
Be certain to include every detail an expert programmer (who does NOT know \
this API), would need to use this API. Include all function names and \
parameters, with short descriptions and gotchas where needed. It would be \
useless to list a function without listing its parameters, no one could \
know how to use it, so be sure to include all the necessary details. \
'Concise' does not mean to leave out important information.${*:-}"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	summary-api "$@"
fi

# version: 0.1.1
