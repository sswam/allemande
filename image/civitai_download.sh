#!/bin/bash -eu

work="$PWD"
tmp=$(mktemp -t -d 'civitai-dl.XXXXXXXX')
cd "$tmp"

for URL; do
	if [[ $URL != "https://"* ]]; then
		URL="https://civitai.com$URL"
	fi
	file=$(curl -s -w "%{filename_effective}\n" -O "$(curl -s -H "Authorization: Bearer $CIVITAI_API_KEY" "$URL")")

	# echo "$file"

	# Fix the filename, remove bogus "."-delimited component before extension

	if [[ "$file" =~ \.[a-zA-Z]{4}\.[^.]*$ ]]; then
		old_file="$file"
		ext="${file##*.}"
		base="${file%.*}"
		new_base="${base%.*}"
		file="$new_base.$ext"
		mv "$old_file" "$file" || true
	fi

	echo "${file%.safetensors}"

	mv "$file" "$work/"
done

rmdir "$tmp"
