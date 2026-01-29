#!/usr/bin/env bash
# [options] query|"" [context ...]
# invoke Ally Chat agents from the command line

# shellcheck disable=SC1007,SC2034  # Disable certain shellcheck rules that conflict with ally options parser syntax

ally-chat-cli() {
	local user= u=${USER^}  # name of user, default to title case of $USER
	local agents=() a=()    # array of agents to invoke
	local responses= n=     # number of responses to expect

	eval "$(ally)"  # Note to AI: This is our magickal options parser and more.

	if [ "${#agents[@]}" = 0 ]; then
		agents=("$ALLEMANDE_LLM_DEFAULT")
	fi

	if [ -z "$responses" ]; then
		responses=${#agents[@]}
	fi

	local query=${1:-}
	shift || true

	local contexts=("$@")

	echo "user: $user"
	echo "agents:"
	lecho "${agents[@]}"
	echo "responses: $responses"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	ally-chat-cli "$@"
fi


