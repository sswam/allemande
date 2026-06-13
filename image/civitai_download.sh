#!/bin/bash -eu
URL=$1
curl -s -w "%{filename_effective}\n" -O "$(curl -s -H "Authorization: Bearer $CIVITAI_API_KEY" "$URL")"
