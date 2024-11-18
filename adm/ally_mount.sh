#!/bin/bash -eu
# ally-mount:	mount the allemande server, or unmount it
u=	# unmount
. opts

umount=$u

ally-mount() {
	mkdir -p $ALLEMANDE_ROOMS_SERVER
	sshfs -o cache=no -o allow_root -o allow_other -o idmap=none $SERVER_ROOMS_SSH $ALLEMANDE_ROOMS_SERVER || true

	portal-mount stt_whisper/www-data
	portal-mount llm_llama/$USER
}

ally-umount() {
	fusermount -u $ALLEMANDE_ROOMS_SERVER || true

	portal-umount stt_whisper/www-data
	portal-umount llm_llama/$USER
}

portal-mount() {
	local portal=$1
	qe rmdir /var/spool/allemande/$portal/* || true
	sshfs -o cache=no -o allow_root -o allow_other -o idmap=none ucm.dev:/var/spool/allemande/$portal /var/spool/allemande/$portal -o cache=no || true
}

portal-umount() {
	local portal=$1
	fusermount -u /var/spool/allemande/$portal || true
	qe rmdir /var/spool/allemande/$portal/* || true
}

if [ "$0" = "$BASH_SOURCE" ]; then
	if [ "$umount" = 1 ]; then
		ally-umount
	else
		ally-mount
	fi
fi
