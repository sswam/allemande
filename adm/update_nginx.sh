#!/usr/bin/env bash
# update the nginx config, adding the JWT secret -----------------------------

set -a -e -u -o pipefail

ALLYCHAT_JWT_SECRET_BINHEX=$(echo -n "$ALLYCHAT_JWT_SECRET" | binhex)

. get-root

set -e -u

cd "$ALLEMANDE_HOME/adm"

rm -f /etc/nginx/sites-available/allemande

umask 0077
sed 's/^\([[:space:]]*auth_jwt_key \)".*";$/\1"'"$ALLYCHAT_JWT_SECRET_BINHEX"'";/' \
	< nginx/sites-available/allemande > /etc/nginx/sites-available/allemande

service nginx reload
