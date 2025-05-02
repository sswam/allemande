#!/bin/bash -eu

. get-root

set -e -u -o pipefail

. /etc/remote_user.conf

user=$1
chroot=${2:-$CHROOT_BASE}

source="/opt/venvs/python3.12-ai/venv"
target="$chroot/home/$user/python3.12-ai/venv"
mkdir -p "$target"{,-upper,-work}
chown "$user:$user" "$target"{,-upper,-work}

mount -t overlay overlay -o lowerdir="$source",upperdir="$target-upper",workdir="$target-work" "$target"
