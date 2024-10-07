#!/bin/bash -eu
# ally-mount:	mount the allemande server, or unmount it
u=	# unmount
. opts

umount=$u

ally-mount() {
	mkdir -p $ALLEMANDE_ROOMS_SERVER
	sshfs -o cache=no -o allow_root -o allow_other -o idmap=none $SERVER_ROOMS_SSH $ALLEMANDE_ROOMS_SERVER || true
	sudo -u allemande qe rmdir /var/spool/allemande/stt_whisper/www-data/* || true
	sudo -u allemande sshfs -o cache=no -o allow_root -o allow_other -o idmap=none ucm.dev:/var/spool/allemande/stt_whisper/www-data /var/spool/allemande/stt_whisper/www-data -o cache=no || true
}

ally-umount() {
	fusermount -u $ALLEMANDE_ROOMS_SERVER || true
	sudo -u allemande fusermount -u /var/spool/allemande/stt_whisper/www-data || true
	sudo -u allemande qe rmdir /var/spool/allemande/stt_whisper/www-data/* || true
}


if [ "$0" = "$BASH_SOURCE" ]; then
	if [ "$umount" = 1 ]; then
		ally-umount
	else
		ally-mount
	fi
fi
