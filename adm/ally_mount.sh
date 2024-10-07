#!/bin/bash -eu
# ally_mount:	mount the allemande server, or unmount it
u=	# unmount
. opts

umount=$u

ally_mount() {
	mkdir -p $ALLEMANDE_ROOMS_SERVER
	sshfs -o cache=no -o allow_root -o allow_other -o idmap=none $SERVER_ROOMS_SSH $ALLEMANDE_ROOMS_SERVER || true
	sudo -u allemande qe rmdir /var/spool/allemande/stt_whisper/www-data/* || true
	sudo -u allemande sshfs -o cache=no -o allow_root -o allow_other -o idmap=none ucm.dev:/var/spool/allemande/stt_whisper/www-data /var/spool/allemande/stt_whisper/www-data -o cache=no || true
}

ally_umount() {
	fusermount -u $ALLEMANDE_ROOMS_SERVER || true
	sudo -u allemande fusermount -u /var/spool/allemande/stt_whisper/www-data || true
	sudo -u allemande qe rmdir /var/spool/allemande/stt_whisper/www-data/* || true
}


if [ "$0" = "$BASH_SOURCE" ]; then
	if [ "$umount" = 1 ]; then
		ally_umount
	else
		ally_mount
	fi
fi
