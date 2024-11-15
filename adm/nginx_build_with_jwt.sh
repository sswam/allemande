#!/bin/bash

set -e -u -o pipefail

NGINX_VERSION=${1:-}

cd ~/soft/

if [ ! -e ngx-http-auth-jwt-module ]; then
	git clone git@github.com:TeslaGov/ngx-http-auth-jwt-module.git
else
	(cd ngx-http-auth-jwt-module; git pull)
fi

if [ -z "$NGINX_VERSION" ]; then
	NGINX_VERSION=$(
		apt-cache policy nginx |
			perl -ne '/ Candidate: (.*)/ && print "$1\n"'
	)
fi
NGINX_VERSION_SOURCE=${NGINX_VERSION%+*}
NGINX_VERSION_ALLY="$NGINX_VERSION_SOURCE+ally1"
NGINX_DIR=nginx-${NGINX_VERSION_SOURCE%-*}
ARCH=$(dpkg --print-architecture)

apt-get source nginx=$NGINX_VERSION

apt-get build-dep -s nginx=$NGINX_VERSION |
	sed -n '/^The following NEW packages will be installed:$/,/^[^ ]/p' |
	grep '^ ' || true > nginx-build-deps
if [ -s nginx-build-deps ]; then
	metadeb nginx-build-deps
fi
sudo apt-get install libjwt-dev libjansson-dev

cd "$NGINX_DIR"

ed debian/rules <<END
/basic_configure_flags
/^$
?--with
i
			--add-module=$HOME/soft/ngx-http-auth-jwt-module \\
.
w
q
END

ed debian/changelog <<END
1
i
nginx ($NGINX_VERSION_ALLY) unstable; urgency=medium

  * Build with ngx-http-auth-jwt-module

 -- Sam Watkins <sam@ucm.dev>  `date -R`

.
w
q
END

debuild -b

cd ..

sudo apt-get install "./nginx_${NGINX_VERSION_ALLY}_$ARCH.deb" "./nginx-common_${NGINX_VERSION_ALLY}_all.deb"
