#!/usr/bin/env bash

# [program and args]
# Run a program without network access

offline() {
	netns=offline n=  # network namespace name
	verbose= v=       # verbose output
	keep= k=         # keep namespace after exit

	eval "$(ally)"

	# Create namespace if it doesn't exist
	if ! ip netns list | grep -q "^$netns"; then
		if [ "$verbose" = 1 ]; then
			echo >&2 "Creating network namespace: $netns"
		fi
		ip netns add "$netns" || die "failed to create netns"
	fi

	# Run command in namespace
	if [ $# -eq 0 ]; then
		die "no command specified"
	fi

	if [ "$verbose" = 1 ]; then
		echo >&2 "Running in network namespace: $netns"
		echo >&2 "Command: $*"
	fi

	local command=$(which "$1") ; shift
	ip netns exec "$netns" sudo -E --preserve-env=PATH,PYTHONPATH,PERL5LIB -u "$SUDO_USER" "$command" "$@"
	status=$?

	# Clean up unless keep option specified
	if [ "$keep" != 1 ]; then
		if [ "$verbose" = 1 ]; then
			echo >&2 "Removing network namespace: $netns"
		fi
		ip netns delete "$netns" || echo >&2 "failed to delete netns"
	fi

	return $status
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	. get_root # Ensure root privileges
	offline "$@"
fi

# version: 0.1.0
