#!/bin/bash
# connect - persistent connect to a server, for quicker ssh commands
login="$1" cmd="$2"

if [ -z "$login" ]; then
	echo >&2 "usage: connect hostname [cmd]"
fi

# Handle Ctrl-C
trap 'echo "Interrupted, Disconnecting: $login" >&2; exit 130' INT

while true; do
	if [ -n "$cmd" ]; then
		ssh -T -oControlMaster=yes -oServerAliveInterval=15 -oServerAliveCountMax=3 "$login" <<END
$cmd
exec sleep infinity
END
	else
		ssh -T -oControlMaster=yes -oServerAliveInterval=15 -oServerAliveCountMax=3 -N "$login"
	fi
	echo "SSH connection terminated, reconnecting: $login"
done
