#!/bin/bash -eu
for url; do
	web-text -- "$url"
	echo
done
