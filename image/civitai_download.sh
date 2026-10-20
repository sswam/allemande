#!/bin/bash -eu

work="$PWD"
tmp=$(mktemp -t -d 'civitai-dl.XXXXXXXX')
cd "$tmp"

for URL; do
	if [[ $URL != "https://"* ]]; then
		URL="https://civitai.com$URL"
	fi
	file=$(
		retry=10
		until curl -s -C - --fail -w "%{filename_effective}\n" -O "$(curl -s -H "Authorization: Bearer $CIVITAI_API_KEY" "$URL")"; do
			echo >&2 "Connection dropped. Retrying and resuming..."
			sleep 3
			retry=$((retry-1))
			if [ "$retry" -le 0 ]; then
				break
			fi
		done
	)

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
