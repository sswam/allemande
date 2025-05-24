#!/usr/bin/env bash

. get_root

# Check if we're connected via SSH
if [ -z "${SSH_CLIENT:-}" ]; then
	exit 0
fi

# Check for cscli command
if ! command -v cscli &> /dev/null; then
	exit 0
fi

# Extract client IP from SSH_CLIENT
client_ip=${SSH_CLIENT%% *}

if [ -z "$client_ip" ]; then
	echo >&2 "Could not determine client IP"
	exit 1
fi

# Check if IP is already whitelisted
if cscli decisions list | grep -w whitelist | fgrep -q "Ip:$client_ip "; then
	exit 0
fi

# Add IP to whitelist
if ! cscli decisions add -i "$client_ip" -t whitelist --duration 168h; then
	echo >&2 "Failed to whitelist IP $client_ip"
	exit 1
fi

# printf 'Successfully whitelisted %s\n' "$client_ip"
