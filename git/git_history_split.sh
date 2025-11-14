#!/usr/bin/env bash
# <file>
# Extract each revision of a file from git history to numbered files

git-history-split() {
	local dir= d= # directory to extract to (default: FILE.d)

	eval "$(ally)"

	local file=${1:?file required}

	# Determine output directory
	local output_dir
	if [ -n "$dir" ]; then
		output_dir=$dir
	else
		output_dir=${file}.d
	fi

	mkdir -p "$output_dir"

	# Get all commit hashes that touched this file, oldest first
	local commits=()
	while IFS= read -r commit; do
		commits+=("$commit")
	done < <(git log --reverse --pretty=format:%H -- "$file")

	if [ "${#commits[@]}" -eq 0 ]; then
		die "no commits found for file: $file"
	fi

	# Extract each revision
	local i=0
	for commit in "${commits[@]}"; do
		local output_file
		printf -v output_file "%s/%04d" "$output_dir" "$i"
		git show "$commit:$file" > "$output_file"
		i=$((i + 1))
	done
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	git-history-split "$@"
fi

# version: 0.1.0
