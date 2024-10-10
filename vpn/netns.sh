#!/bin/bash -eu
. get_root
n=
. opts
netns=$1
shift
if [ -z "$n" ]; then
	qe ip netns add "$netns" || true
fi
ip netns exec "$netns" "${@:-$SHELL}"
