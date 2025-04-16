#!/bin/bash -eu
# web-uninstall: uninstall nginx config

. get_root

# restore the original haproxy config ----------------------------------------

mv /etc/haproxy/haproxy.cfg.dist /etc/haproxy/haproxy.cfg

# remove nginx sites ---------------------------------------------------------

cd "$ALLEMANDE_HOME/adm/nginx/sites-available"
for site in *; do
	rm -f "/etc/nginx/sites-enabled/$site"
done

# remove nginx config --------------------------------------------------------

cd "$ALLEMANDE_HOME/adm/nginx"

find . -type f \( -name ".*" -o -print \) |
while read conf; do
	rm -f "/etc/nginx/$conf"
done

service nginx restart
service haproxy restart
