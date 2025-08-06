#!/bin/bash
# connects - connect to all servers listed in ~/.peers

cd /
H=$(hostname -f)
PEERS_FILE=~/.peers
PIDS=()

# Function to handle SIGINT
cleanup() {
	echo -e "\nReceived interrupt, killing all connections..."
	for pid in "${PIDS[@]}"; do
		kill -INT "$pid" 2>/dev/null
	done
	exit 1
}

# Set up signal handler
trap cleanup SIGINT

# Check if peers file exists
if [ ! -f "$PEERS_FILE" ]; then
	echo "Error: $PEERS_FILE not found"
	exit 1
fi

# Read the peers file
while IFS=$'\t' read -r hostname alias cmd || [ -n "$hostname" ]; do
	# Skip empty lines and comments
	[[ -z "$hostname" || "$hostname" =~ ^# ]] && continue

	# Use alias if provided, otherwise use hostname
	target="${alias:-$hostname}"

	# Don't connect to our own hostname
	if [ "$hostname" == "$H" ]; then
		continue
	fi

	# Start connection and store PID
	(echo "connect $target"; connect "$target" "$cmd") &
	PIDS+=($!)
done < "$PEERS_FILE"

# Wait for all connections to complete
wait
