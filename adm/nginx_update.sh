#!/usr/bin/env bash
# update the nginx config, adding the JWT secret -----------------------------

set -a -e -u -o pipefail

ALLYCHAT_JWT_SECRET_BINHEX=$(echo -n "$ALLYCHAT_JWT_SECRET" | binhex)

. get-root

set -e -u

cd "$ALLEMANDE_HOME/adm/nginx"

umask 0077

ALLEMANDE_DOMAIN_ESC=${ALLEMANDE_DOMAIN//./\\.}

find . -type f \( -name ".*" -o -print \) |
while read file; do
	rm -f "/etc/nginx/$file"
	envsubst '$ALLYCHAT_JWT_SECRET_BINHEX,$ALLEMANDE_DOMAIN,$ALLEMANDE_DOMAIN_ESC' < "$file" > "/etc/nginx/$file"
done

service nginx reload || service nginx start
service nginx status
