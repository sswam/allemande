#!/bin/bash
. opts

url=$1
shift

# Support github.com/a/b or plain a/b by assuming github.
if [[ $url == https://github.com/* ]]; then
	url=${url%/}
	url="git@github.com:${url#https://github.com/}.git"
elif [[ $url == github.com/* ]]; then
	url=${url%/}
	url="git@github.com:${url#github.com/}.git"
elif [[ $url == */* ]] && [[ $url != *://* ]]; then
	url=${url%/}
	url="git@github.com:${url}.git"
fi

git clone "${OPTS[@]}" "$url" "$@"

# shellcheck disable=SC1091  # opts may be provided elsewhere or by env
