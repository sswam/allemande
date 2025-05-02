#!/bin/bash

. /etc/remote_user.conf

USER_UID=$(id -u "$PAM_USER")

if [ "$USER_UID" -lt "$REMOTE_UID_MIN" ] || [ "$USER_UID" -gt "$REMOTE_UID_MAX" ]; then
	exit 0
fi

loginctl set-slice "$PAM_USER" "remote-user@$PAM_USER.slice"

exit 0
