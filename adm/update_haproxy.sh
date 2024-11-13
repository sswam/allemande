#!/usr/bin/env bash
# update the haproxy config -------------------------------------------------

. get-root

set -e -u

cd "$ALLEMANDE_HOME/adm"

if [ ! -e /etc/haproxy/haproxy.cfg.dist ]; then
	mv /etc/haproxy/haproxy.cfg /etc/haproxy/haproxy.cfg.dist
fi

rm -f /etc/haproxy/haproxy.cfg

include < haproxy/haproxy.cfg > /etc/haproxy/haproxy.cfg

service haproxy reload
