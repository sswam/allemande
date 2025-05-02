#!/bin/bash

. get-root

set -e -u -o pipefail

. /etc/remote_user.conf

user="$1"
fullname="$2"
chroot="${3:-$CHROOT_BASE}"

adduser --firstuid $REMOTE_UID_MIN --lastuid $REMOTE_UID_MAX --firstgid $REMOTE_UID_MIN --lastgid $REMOTE_UID_MAX --disabled-password --gecos "$fullname" "$user"
deluser "$user" users
adduser "$user" "$REMOTE_GROUP"
usermod --home "/home/$user" "$user"

for file in passwd shadow group gshadow; do
	grep "^$user:" /etc/$file >> "$chroot/etc/$file"
done
