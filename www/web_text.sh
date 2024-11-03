#!/bin/bash -eu
# wget_text:	get a webpage as simple plain text / markdown

s=	sleep=	# use selenium-get and sleep before dumping
. opts
sleep=${sleep:-$s}

url="$1"
tmp=`mktemp`

get() {
	if [ "$s" ]; then
		selenium-get -s "$s" "$url"
	else
		WG_OPTS=-nv wg -O=- "$url"
	fi
}

get | htmldebloater > "$tmp"
pandoc-dump "$tmp" "$url"
rm "$tmp"
