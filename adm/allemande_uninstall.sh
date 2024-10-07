#!/bin/bash -eu

# remove allemande user and ports directory

. get_root

rm -rf "$ALLEMANDE_PORTS"
userdel "$ALLEMANDE_USER" || true
rm -f /etc/cron.d/allemande
