#!/bin/bash
. opts

url=$1
shift

if [[ $url == https://github.com/* ]]; then
	url=${url%/}
	url="git@github.com:${url#https://github.com/}.git"
fi

git clone "${OPTS[@]}" "$url" "$@"
