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

cd "$ALLEMANDE_HOME/js"
if [ ! -e mousetrap ]; then
	git clone https://github.com/ccampbell/mousetrap
fi

# copy rooms.dict to rooms

cd "$ALLEMANDE_HOME"

if [ ! -d "rooms" ]; then
	cp -a rooms.dist rooms
fi

# install the webchat web app ------------------------------------------------

cd "$ALLEMANDE_HOME/webchat"

mkdir -p "$ALLEMANDE_HOME/rooms"
mkdir -p files
mode 771 rooms files

if [ ! -e .htpasswd ]; then
	touch .htpasswd
fi

mode 640 .htpasswd static/logout/.htpasswd

ln -sfT $PWD /var/www/allychat

# set up the rooms -----------------------------------------------------------

cd rooms

mode 660 *.bb *.html
mode 440 -.bb -.html

# install the nginx config and sites -----------------------------------------

cd "$ALLEMANDE_HOME/adm/nginx"
find . -type f \( -name ".*" -o -print \) |
while read conf; do
	dir=$(dirname "$conf")
	ln -sf "$PWD/$conf" -t /etc/nginx/$dir/
done

# install the nginx sites properly -------------------------------------------

cd "$ALLEMANDE_HOME/adm"

./nginx_update.sh

# install the haproxy config -------------------------------------------------

cd "$ALLEMANDE_HOME/adm"

./haproxy_update.sh

# restart services -----------------------------------------------------------

service nginx stop
service haproxy stop
service nginx start
service haproxy start
