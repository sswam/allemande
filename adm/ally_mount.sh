#!/bin/bash -eu
# ally-mount:	mount the allemande server, or unmount it
u=	# unmount
. opts

umount=$u

ally-mount() {
	mkdir -p $ALLEMANDE_ROOMS_SERVER
	sshfs -o cache=no -o allow_root -o allow_other -o idmap=none $SERVER_ROOMS_SSH $ALLEMANDE_ROOMS_SERVER || true

	for client in $ALLEMANDE_PORTAL_CLIENTS; do
		if [ "$client" = "$HOSTNAME" ]; then
			continue
		fi
		for service in $ALLEMANDE_MODULES; do
			portal-mount $client $service/${client}_www-data
			portal-mount $client $service/${client}_$USER
		done
	done
}

ally-umount() {
	fusermount -u $ALLEMANDE_ROOMS_SERVER || true

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

portal-mount() {
	local client=$1
	local portal=$2
	local portal_path=$ALLEMANDE_PORTALS/$portal
	mkdir -p $portal_path
	qe rmdir $portal_path/* || true
	sshfs -o cache=no -o allow_root -o allow_other -o idmap=none $client:$portal_path $portal_path -o cache=no || true
}

portal-umount() {
	local portal=$1
	local portal_path=$ALLEMANDE_PORTALS/$portal
	fusermount -u $portal_path || true
	qe rmdir $portal_path/* || true
}

if [ "$0" = "$BASH_SOURCE" ]; then
	if [ "$umount" = 1 ]; then
		ally-umount
	else
		ally-mount
	fi
fi
