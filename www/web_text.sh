#!/bin/bash -eu
# wget_text:	get a webpage as simple plain text / markdown

s=	sleep=	# use selenium-get and sleep before dumping
. opts
sleep=${sleep:-$s}

url="$1"
tmp=`mktemp`
tmp2=`mktemp`

get() {
	if [ "$s" ]; then
		selenium-get -s "$s" "$url"
	else
		WG_OPTS=-nv wg -O=- "$url"
	fi
}

get > "$tmp"
title=`html-title < "$tmp"`
<"$tmp" www-clean | htmldebloater > "$tmp2"
pandoc-dump -t="$title" "$tmp2" "$url" | www-clean -m markdown
rm "$tmp" "$tmp2"
