#!/usr/bin/env bash

# [server name]
# Open xterminals for allemande services locally and on server

xt-allemande() {
	# shellcheck disable=SC2153
	local server= s="$SERVER"  # server to connect to
	local local= l=            # view only local services
	local remote= r=           # view only remote services
	local kill= k=             # close all terminals (doesn't kill services)
	local wait= w=0            # wait a little between opening terminals

	eval "$(ally)"

	# Handle kill option
	if [ "$kill" = 1 ]; then
		# Find xterm processes running our specific commands
		# Match xterms running either "sxw allemande" or "sshc v* sxw allemande"
		pkill -f 'xterm.*sxw allemande'
		pkill -f 'xterm.*sshc v.*sxw allemande'
		echo >&2 "Closed allemande service terminals"
		return 0
	fi

	# Compute remote_services and local_services from all_services in a single pass
	local remote_services=()
	local local_services=()
	local service

	for host_service in "${all_services[@]}"; do
		service="${host_service#*:}"
		case "$host_service" in
			r:*) remote_services+=("$service") ;;
			l:*) local_services+=("$service") ;;
			*) die "Unknown service type: $host_service" ;;
		esac
	done

	# Split the current i3 window vertically
	i3-msg split h || true

	# If neither local or remote is specified, show both
	if [ -z "$local" ] && [ -z "$remote" ]; then
		local=1
		remote=1
	fi

	# Local services
	if [ "$local" = 1 ] && [ "$remote" != 1 ]; then
		for service in "${local_services[@]}"; do
			echo -n "$service "
			xt sxw allemande "$service" &
			sleep $wait
		done
		echo
	fi

	# Remote services
	if [ "$remote" = 1 ] && [ "$local" != 1 ]; then
		for service in "${remote_services[@]}"; do
			echo -n "$service "
			xt sshc v"$server" sxw allemande "$service" &
			sleep $wait
		done
		echo
	fi

	# Both: open in specified order
	if [ "$local" = 1 ] && [ "$remote" = 1 ]; then
		for host_service in "${all_services[@]}"; do
			service="${host_service#*:}"
			echo -n "$service "
			if [[ " ${local_services[*]} " == *" $service "* ]]; then
				xt sxw allemande "$service" &
			else
				xt sshc v"$server" sxw allemande "$service" &
			fi
			sleep $wait
		done
		echo
	fi
}

all_services=(r:wat r:brain l:image l:forge l:llm l:whisper r:chat-api r:stream r:bb2html r:auth r:watch r:shortcuts r:build-ui l:notify l:vup)

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	xt-allemande "$@"
fi

# version: 0.1.2
