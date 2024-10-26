#!/bin/bash -eu
# huggingface-get: download a model from huggingface.co without eating double disk

. confirm

n=

. opts

if [ -n "$n" ]; then
	run=cat
else
	run="sh -v"
fi

repo=${1:-.}

clone=1

repo=${repo%/tree/main}
repo=${repo%/}

if [[ $repo == https:* ]]; then
	url="$repo"
	repo="${url#https://huggingface.co/}"
fi

#echo "url: $url"
#echo "repo: $repo"

if [ -d "$repo" ]; then
	cd "$repo"
	url=`git remote get-url origin`
	clone=0
else
	url="https://huggingface.co/$repo"
fi

base=$(basename "$repo")
dir=$(dirname "${repo#/}")

nt "$base"

if [ "$repo" = "$url" ]; then
	echo >&2 "error: not a huggingface.co url: $url"
	exit 1
fi

if [ "$clone" = 1 ]; then
	mkdir -p "$dir"
	cd "$dir"
	GIT_LFS_SKIP_SMUDGE=1 v git clone "$url"
	cd "$base"
fi

git lfs ls-files | cut -d' ' -f3- |
while read file; do
	file_url="https://huggingface.co/$repo/resolve/main/$file"
	dir=$(dirname "$file")
	# if "$file" is small, then remove it; it's likely the git lfs pointer, not the model file
	if [ -e "$file" ] && [ $(stat -c%s "$file") -lt 1000 ]; then
		rm -v "$file" >&2   # WTF rm, write messages on stdout?!
		echo
	fi
	printf "%q " wget --header="Authorization: Bearer $HUGGINGFACE_API_TOKEN" -P "$dir" -c "$file_url"
	echo
done |
$run

#ls | grep -v '2\.7B' | while read M; do (cd "$M"; git lfs ls-files | k 3 | while read file; do url="https://huggingface.co/cerebras/$(basename `git-root`)/resolve/main/$file"; echo "wget -c $url"; done | sh ); done
