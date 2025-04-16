#!/bin/bash -eu
# web-install: set permissions for the web app and install nginx config

. get-root

mode() {
	mode=$1 ; shift
	chown $SUDO_USER:www-data -- "$@"
	chmod $mode -- "$@"
}

# -------- install the allemande website -------------------------------------

ln -sfT "$ALLEMANDE_HOME/site" /var/www/allemande

# -------- install mousetrap library -----------------------------------------

# cd "$ALLEMANDE_HOME/js"
# if [ ! -e mousetrap ]; then
# 	git clone https://github.com/ccampbell/mousetrap
# fi

# -------- copy rooms.dist to rooms ------------------------------------------

cd "$ALLEMANDE_HOME"

if [ ! -d "rooms" ]; then
	cp -a rooms.dist rooms
fi

find rooms -type d | xa chown $SUDO_USER:www-data --
find rooms -type d | xa chmod 2775
find rooms -type f | xa chown $SUDO_USER:www-data --
find rooms -type f | xa chmod 660

# -------- install the webchat web app ---------------------------------------

cd "$ALLEMANDE_HOME/webchat"

if [ ! -e .htpasswd ]; then
	touch .htpasswd
fi

mode 640 .htpasswd

ln -sfT $PWD /var/www/allychat

# -------- set up the rooms --------------------------------------------------

cd rooms

mode 660 *.bb *.html || true

# -------- install the nginx config and sites --------------------------------

cd "$ALLEMANDE_HOME/adm"

if [ ! -e /etc/nginx/banned_ips.conf ]; then
	touch /etc/nginx/banned_ips.conf
	mode 600 /etc/nginx/banned_ips.conf
fi

cd /etc/nginx/sites-enabled
rm -f default
ln -sf ../sites-available/letsencrypt .

cd "$ALLEMANDE_HOME/adm"

./nginx_update.sh

# -------- install the haproxy config ----------------------------------------

./haproxy_update.sh

# -------- set up SSL certificates using letsencrypt / certbot ---------------

if [ ! -s "/etc/letsencrypt/live/$ALLEMANDE_DOMAIN/fullchain.pem" ]; then
	service nginx stop
	service nginx start
	certbot certonly --webroot -w /var/www/html -d "$ALLEMANDE_DOMAIN" -d chat."$ALLEMANDE_DOMAIN" -d rooms."$ALLEMANDE_DOMAIN"
fi

# -------- enable the sites --------------------------------------------------

cd /etc/nginx/sites-enabled
for site in allemande chat rooms; do
	ln -sf ../sites-available/$site .
done

# -------- restart services --------------------------------------------------

service haproxy stop
service nginx stop
service nginx start
service haproxy start
