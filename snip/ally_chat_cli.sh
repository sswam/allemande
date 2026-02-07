#!/usr/bin/env bash
# [options] query|"" [context ...]
# invoke an Ally Chat agent from the command line

# shellcheck disable=SC1007,SC2034  # Disable certain shellcheck rules that conflict with ally options parser syntax

ally-chat-cli() {
	local user= u="User"                     # name of user
	local agent= a="$ALLEMANDE_LLM_DEFAULT"  # agent to invoke

	eval "$(ally)"  # Note to AI: This is our magickal options parser and more.

	local query=${1:-}
	shift || true

	local contexts=("$@")

	echo "user: $user"
	echo "agent: $agent"
	echo "query: $query"
	echo "contexts: ${contexts[*]}"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	ally-chat-cli "$@"
fi


