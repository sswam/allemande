#!/usr/bin/env bash

# [server name]
# Open xterminals for allemande services locally and on server

remote_services=(chat-api stream watch bb2html auth build-ui brain wat)
local_services=(llm image a1111 vup)

xt-allemande() {
	local server= s=$SERVER   # server to connect to
	local local= l=           # view only local services
	local remote= r=          # view only remote services

	eval "$(ally)"

	# If neither local or remote is specified, show both
	if [ -z "$local" ] && [ -z "$remote" ]; then
		local=1
		remote=1
	fi

	# Local services
	if [ "$local" = 1 ]; then
		for service in "${local_services[@]}"; do
			xt -e sxw allemande "$service" &
			sleep 0.1
		done
	fi

	# Remote services
	if [ "$remote" = 1 ]; then
		for service in "${remote_services[@]}"; do
			xt -e sshc "$server" sxw allemande "$service" &
			sleep 0.1
		done
	fi
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	xt-allemande "$@"
fi

# version: 0.1.0
