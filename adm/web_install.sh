#!/bin/bash -eu
# web-install: set permissions for the web app and install nginx config

. get-root

mode() {
	mode=$1 ; shift
	chown $SUDO_USER:www-data -- "$@"
	chmod $mode -- "$@"
}

# install the allemande.ai website -------------------------------------------

ln -sfT "$ALLEMANDE_HOME/site" /var/www/allemande

# install mousetrap library --------------------------------------------------

# cd "$ALLEMANDE_HOME/js"
# if [ ! -e mousetrap ]; then
# 	git clone https://github.com/ccampbell/mousetrap
# fi

# copy rooms.dist to rooms

cd "$ALLEMANDE_HOME"

if [ ! -d "rooms" ]; then
	cp -a rooms.dist rooms
fi

# install the webchat web app ------------------------------------------------

cd "$ALLEMANDE_HOME/webchat"

mkdir -p "$ALLEMANDE_HOME/rooms"
mode 771 rooms

if [ ! -e .htpasswd ]; then
	touch .htpasswd
fi

mode 640 .htpasswd static/logout/.htpasswd

ln -sfT $PWD /var/www/allychat

# set up the rooms -----------------------------------------------------------

cd rooms

mode 660 *.bb *.html || true

# install the nginx config and sites -----------------------------------------

cd "$ALLEMANDE_HOME/adm"

if [ ! -e /etc/nginx/banned_ips.conf ]; then
	touch /etc/nginx/banned_ips.conf
	mode 600 /etc/nginx/banned_ips.conf
fi

rm -f /etc/nginx/sites-enabled/default

./nginx_update.sh

cd /etc/nginx/sites-enabled
for site in chat rooms; do
	ln -sf ../sites-available/$site .
done

# install the haproxy config -------------------------------------------------

cd "$ALLEMANDE_HOME/adm"

./haproxy_update.sh

# restart services -----------------------------------------------------------

service haproxy stop
service nginx stop
service nginx start
service haproxy start
