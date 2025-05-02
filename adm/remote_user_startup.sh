#!/bin/bash

set -e -u -o pipefail

. /etc/remote_user.conf

# mount
mount "$CHROOT_BASE/usr"
mount "$CHROOT_BASE/proc"
mount "$CHROOT_BASE/sys"
mount "$CHROOT_BASE/sys/fs/cgroup"
mount "$CHROOT_BASE/dev/pts"
