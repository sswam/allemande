#!/bin/bash -eu
# wget_text:	get a webpage as simple plain text / markdown

url="$1"
tmp=`mktemp`
WG_OPTS=-nv wg -O=- "$url" | htmldebloater > "$tmp"
pandoc-dump "$tmp" "$url"
rm "$tmp"
