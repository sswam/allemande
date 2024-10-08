#!/bin/bash -eu
# web-install: set permissions for the web app and install nginx config

. get_root

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

# install the webchat web app ------------------------------------------------

cd "$ALLEMANDE_HOME/webchat"

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
mode 440 -.bb -.html demo.bb demo.html adult/demo.bb adult/demo.html

# install the nginx config and sites -----------------------------------------

cd "$ALLEMANDE_HOME/adm/nginx"
find . -type f \( -name ".*" -o -print \) |
while read conf; do
	dir=$(dirname "$conf")
	ln -sf "$PWD/$conf" -t /etc/nginx/$dir/
done

# enable the nginx sites -----------------------------------------------------

cd "sites-available"
for site in *; do
	ln -sf "../sites-available/$site" /etc/nginx/sites-enabled/
done

# install the haproxy config -------------------------------------------------

cd "$ALLEMANDE_HOME/adm"

if [ ! -L /etc/haproxy/haproxy.cfg ]; then
	mv /etc/haproxy/haproxy.cfg /etc/haproxy/haproxy.cfg.dist
fi
 
ln -sf "$PWD/haproxy/haproxy.cfg" -t /etc/haproxy/

service nginx stop
service haproxy stop
service nginx start
service haproxy start
