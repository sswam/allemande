#!/bin/bash -eu
host=$(basename "$0" .sh)
domainname=$(dnsdomainname)

# check for the host in our VPNs
if grep -q "^Host v$host\$" ~/.ssh/config; then
	host="v$host"
else
  host=$host.$domainname
fi

if [ $# -gt 0 ]; then
  exec sshc "$host" "$@"
fi
exec ssh "$host"
