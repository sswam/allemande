#!/bin/bash

set -e -u -o pipefail

. /etc/remote_user.conf

chroot=${1:-$CHROOT_BASE}

echo "writable directories in chroot"
find "$chroot" -type d -writable
echo

echo "writable entires in chroot protected paths"
find "$chroot" \( -path "$chroot/home" -o -path "$chroot/tmp" -o -path "$chroot/var/tmp" -o -type l -o -path "$chroot/dev/null" -o -path "$chroot/dev/zero" -o -path "$chroot/dev/urandom" -o -path "$chroot/dev/tty" \) -prune -o -writable -print
echo

echo mounted filesystems
mount | fgrep " $chroot" || true
echo

echo unexpected device nodes
find "$chroot" \( -path "$chroot/dev/null" -o -path "$chroot/dev/zero" -o -path "$chroot/dev/urandom" -o -path "$chroot/dev/tty" -o -path "$chroot/dev/console" \) -prune -o -type c,b -print
echo

echo setuid binaries
find "$chroot" -perm -4000
echo

echo setgid binaries
find "$chroot" -perm -2000
echo
