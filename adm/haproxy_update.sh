#!/usr/bin/env bash
# update the haproxy config -------------------------------------------------

. get-root

set -e -u

cd "$ALLEMANDE_HOME/adm"

if [ ! -e /etc/haproxy/haproxy.cfg.dist ]; then
	mv /etc/haproxy/haproxy.cfg /etc/haproxy/haproxy.cfg.dist
fi

if [ ! -e /etc/haproxy/haproxy-clients.cfg ]; then
	touch /etc/haproxy/haproxy-clients.cfg
fi

rm -f /etc/haproxy/haproxy.cfg

(
	echo "# DERIVED FILE: DO NOT EDIT!"
	envsubst '$ALLEMANDE_DOMAIN' < "haproxy/haproxy.cfg" | include
) > /etc/haproxy/haproxy.cfg

service haproxy reload
