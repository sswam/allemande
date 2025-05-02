#!/bin/bash

set -e -u -o pipefail

. /etc/remote_user.conf

USER_UID=$(id -u "$PAM_USER")

if [ "$USER_UID" -lt "$REMOTE_UID_MIN" ] || [ "$USER_UID" -gt "$REMOTE_UID_MAX" ]; then
	exit 0
fi

exec >/tmp/remote_user_debug.log 2>&1

loginctl attach "remote-user@$PAM_USER.slice" "$PAM_USER"
