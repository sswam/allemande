#!/bin/bash

set -e -u -o pipefail

. /etc/remote_user.conf

user="$1"
chroot="${2:-$CHROOT_BASE}"

if ! [[ "$1" =~ ^[a-z][-a-z0-9]*$ ]]; then
       	echo >&2 "Invalid username format"
	exit 1
fi

move-rubbish /home/$user || true
userdel "$user" || true

if [ -z "$chroot" ]; then
	exit
fi

for file in passwd shadow group gshadow; do
	sed -i "/^$user:/d" "$chroot/etc/$file" || true
done
