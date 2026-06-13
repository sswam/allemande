#!/bin/bash -eu
if [ "${1:-}" == -p ]; then
	shift
	export https_proxy="https://127.0.0.1:3128"
fi
for url; do
	web-text -- "$url"
	echo
done
