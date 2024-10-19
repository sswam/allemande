#!/bin/bash
#
# Run the LLM chatbot with the specified settings

eval "$(ally)"

v ally-chat -v -m "$LLM_MODEL" -w "$CHATPATH" -c "$ALLEMANDE_HOME/config/llm_llama/experiment.yaml" \
	--delim $'\n' -u "$user" -b "$bot" -n "$TOKEN_LIMIT" --ignore-shrink "$@"
# --ignore "$user:" "$@"
# not using options: -r --no-trim --get-roles-from-history
