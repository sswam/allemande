#!/bin/bash -eu
# net-watch:	Watch the network status and run jobs when it goes up or down

h="google.com ucm.dev"	# hosts to ping, if one is up, net is up
i=10	# sleep interval in seconds
W=5	# ping timeout in seconds
u=	# script to run when network goes up
d=	# script to run when network goes down

. opts

hosts=$h
interval=$i
ping_timeout=$W

net_status=0

check_network() {
	local host
	# we assume the network is good if any host in the list is reachable
	fail=1
	for host in $HOSTS; do
		ping -c 1 -W $ping_timeout "$host" > /dev/null 2>&1 && fail=0 && break
	done
	return $fail
}

now() {
	date +%F\ %T
}

msg() {
	echo "`now`: $*"
}

# Check if we have an initial connection
if check_network; then
	net_status=1
	msg "Initial connection status: UP"
else
	msg "Initial connection status: DOWN"
fi

# Infinite loop to check the network status
while true; do
	if check_network; then
		if [ "$net_status" -eq 0 -a -n "$u" ]; then
			msg "Network is back up, running up job"
			$u
		elif [ "$net_status" -eq 0 ]; then
			msg "Network is back up"
		fi
		net_status=1
	else
		if [ "$net_status" -eq 1 -a -n "$d" ]; then
			msg "Network is down, running down job"
			$d
		elif [ "$net_status" -eq 1 ]; then
			msg "Network is down"
		fi
	fi
	sleep $interval
done
