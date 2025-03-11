#!/usr/bin/env bash
# update the nginx config, adding the JWT secret -----------------------------

set -a -e -u -o pipefail

ALLYCHAT_JWT_SECRET_BINHEX=$(echo -n "$ALLYCHAT_JWT_SECRET" | binhex)

. get-root

set -e -u

cd "$ALLEMANDE_HOME/adm"

cd nginx/sites-available

umask 0077

for site in *; do
	rm -f "/etc/nginx/sites-available/$site"
	sed 's/^\([[:space:]]*auth_jwt_key \)".*";$/\1"'"$ALLYCHAT_JWT_SECRET_BINHEX"'";/' \
		< "$site" > /etc/nginx/sites-available/"$site"
done

service nginx reload || service nginx start
service nginx status
