#!/bin/bash -eu
cd "$ALLEMANDE_HOME"
mkdir -p rooms.extra rooms.extra.raw rooms.extra.cache || true
fusermount -u rooms.extra || true
pkill -f "sshfs.*rooms.extra" || true
fusermount -u rooms.extra.raw || true
# sshfs -o allow_other -p 2222 localhost:rooms/ rooms.extra
# TODO not hard code VPN IP address

# sshfs -o allow_other 10.0.1.50:rooms/ rooms.extra

sshfs -o allow_other -o kernel_cache,noforget,remember=86400,dcache_timeout=86400,dcache_stat_timeout=86400,dcache_link_timeout=86400,dcache_dir_timeout=86400,entry_timeout=86400,attr_timeout=86400,negative_timeout=86400,dcache_max_size=100000 10.0.1.50:rooms/ rooms.extra # rooms.extra.raw
# mcachefs -o cache=rooms.extra.cache,metafile=rooms.extra.meta,journal=rooms.extra.journal rooms.extra.raw rooms.extra
