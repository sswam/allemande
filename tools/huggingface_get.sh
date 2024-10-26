#!/usr/bin/env bash

# [repo]
# Download a model from huggingface.co without duplicating disk usage
# This script clones a Hugging Face repository and downloads LFS files efficiently

huggingface-get() {
	local n= # dry run mode
	local repo=${1:-.}

	eval "$(ally)"

	local run="sh -v"
	if [ -n "$n" ]; then
 	        run="cat"
	fi

	repo=${repo%/tree/main}
	repo=${repo%/}

	local url="$repo"

	if [[ $repo == https:* ]]; then
		url="$repo"
		repo="${url#https://huggingface.co/}"
	fi

	local base dir clone=1
	base=$(basename "$repo")
	dir=$(dirname "${repo#/}")

	nt "$base"

	if [ -d "$repo" ]; then
		cd "$repo" || die "Failed to change directory to $repo"
		url=$(git remote get-url origin)
		clone=0
	else
		url="https://huggingface.co/$repo"
	fi

	if [ "$repo" = "$url" ]; then
		echo >&2 "error: not a huggingface.co url: $url"
		exit 1
	fi

	if [ "$clone" = 1 ]; then
		mkdir -p "$dir"
		cd "$dir" || die "Failed to change directory to $dir"
		GIT_LFS_SKIP_SMUDGE=1 v git clone "$url"
		cd "$base" || die "Failed to change directory to $base"
	fi

	git lfs ls-files | cut -d' ' -f3- | while IFS= read -r file; do
		file_url="https://huggingface.co/$repo/resolve/main/$file"
		file_dir=$(dirname "$file")

		# if "$file" is small, then remove it; it's likely the git lfs pointer, not the model file
		if [ -e "$file" ] && [ "$(stat -c%s "$file")" -lt 1000 ]; then
			rm -v "$file" >&2
			echo
		fi
		printf "%s " wget --header="Authorization: Bearer $HUGGINGFACE_API_TOKEN" -P "$file_dir" -c "$file_url"
		echo
	done |
	$run
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	huggingface-get "$@"
fi

# version: 0.1.1
