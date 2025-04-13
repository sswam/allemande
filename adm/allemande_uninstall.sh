#!/bin/bash -eu

# remove allemande user and portals directory

. get_root

rm -rf "$ALLEMANDE_PORTALS"
userdel "$ALLEMANDE_USER" || true
groupdel "$ALLEMANDE_USER" || true
groupdel chatuser || true
rm -f /etc/cron.d/allemande
