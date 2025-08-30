#!/bin/bash -eu
# ally-mount:	mount the allemande server, or unmount it
u=	# unmount
. opts

umount=$u

DEFAULT_TEST_TIMEOUT=5
CONNECT_TIMEOUT=10
SERVER_ALIVE_INTERVAL=60
SERVER_ALIVE_COUNT_MAX=3

# prevent running this script concurrently
LOCKDIR="$ALLEMANDE_HOME/.mount_lock"

# Clean up lockfile on exit
trap 'rm -rf "$LOCKDIR"' EXIT

# Try to create lockfile, wait if already locked
while ! mkdir "$LOCKDIR" 2>/dev/null; do
    echo "Script is already running (lockdir exists: $LOCKDIR)"
    sleep 1
done

ally-mount() {
	mkdir -p $ALLEMANDE_ROOMS_SERVER # $ALLEMANDE_VISUAL/person

	safe-mount v$SERVER_ROOMS_SSH $ALLEMANDE_ROOMS_SERVER .gitignore
	# safe-mount $SERVER_PERSON_SSH $ALLEMANDE_VISUAL/person .gitignore

	for client in $ALLEMANDE_PORTAL_CLIENTS; do
		if [ "$client" = "$HOSTNAME" ] || [ "$client" = "v$HOSTNAME" ]; then
			continue
		fi
		for service in $ALLEMANDE_MODULES; do
			portal-mount $client $service/${client}_www-data
			portal-mount $client $service/${client}_$USER
		done
	done
}

ally-umount() {
	fusermount -uz $ALLEMANDE_ROOMS_SERVER || true
	# fusermount -uz $ALLEMANDE_VISUAL/person || true

	for client in $ALLEMANDE_PORTAL_CLIENTS; do
		if [ "$client" = "$HOSTNAME" ]; then
			continue
		fi
		for service in $ALLEMANDE_MODULES; do
			portal-umount $service/${client}_www-data
			portal-umount $service/${client}_$USER
		done
	done
}

safe-mount() {
	local ssh_path=$1
	local mount_point=$2
	local test_path=${3:-""}
	local test_timeout=${4:-$DEFAULT_TEST_TIMEOUT}

	# Create directory if needed
	mkdir -p "$mount_point"

	# Check if already mounted and working
	if mountpoint -q "$mount_point"; then
		if [ -z "$test_path" ] || timeout "$test_timeout" test -e "$mount_point/$test_path" 2>/dev/null; then
			echo >&2 "Already mounted: $mount_point"
			return 0
		fi
	fi

	safe-umount "$mount_point"

	# Attempt mount
	sshfs -o cache=no \
		-o allow_root \
		-o allow_other \
		-o idmap=none \
		-o ConnectTimeout=${CONNECT_TIMEOUT} \
		-o ServerAliveInterval=${SERVER_ALIVE_INTERVAL} \
		-o ServerAliveCountMax=${SERVER_ALIVE_COUNT_MAX} \
		"$ssh_path" "$mount_point"

	# Verify mount worked
	if ! mountpoint -q "$mount_point"; then
		return 1
	fi

	# If test path specified, verify it exists
	if [ -n "$test_path" ]; then
		timeout "$test_timeout" test -e "$mount_point/$test_path"
		return $?
	fi

	return 0
}

safe-umount() {
	local mount_point=$1
	while fusermount -uz "$mount_point" 2>/dev/null; do :; done

	# Clean up any empty directories under the mount point
	rmdir "$mount_point"/* 2>/dev/null || true
}

portal-mount() {
	local client=$1
	local portal=$2
	local portal_path=$ALLEMANDE_PORTALS/$portal

	safe-mount "v$client:$portal_path" "$portal_path" "todo"
}

portal-umount() {
	local portal=$1
	local portal_path=$ALLEMANDE_PORTALS/$portal
	safe-umount "$portal_path"
}

if [ "$0" = "$BASH_SOURCE" ]; then
	if [ "$umount" = 1 ]; then
		ally-umount
	else
		ally-mount
	fi
fi
