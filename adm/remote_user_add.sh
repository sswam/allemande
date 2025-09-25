#!/bin/bash

set -e -u -o pipefail

. /etc/remote_user.conf

user="$1"
fullname="$2"
chroot="${3:-$CHROOT_BASE}"

if ! [[ "$1" =~ ^[a-z][-a-z0-9]*$ ]]; then
       	echo >&2 "Invalid username format"
	exit 1
fi

v adduser --firstuid $REMOTE_UID_MIN --lastuid $REMOTE_UID_MAX --firstgid $REMOTE_UID_MIN --lastgid $REMOTE_UID_MAX --disabled-password --gecos "$fullname" "$user"
v deluser "$user" users
v adduser "$user" "$REMOTE_GROUP"
# v usermod --home "/home/$user" "$user"

for file in passwd shadow group gshadow; do
	grep "^$user:" /etc/$file >> "$chroot/etc/$file"
done
