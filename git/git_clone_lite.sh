#!/usr/bin/env bash

# [repository-url] [subdirectory]
# Clones a specific subdirectory from a git repository with depth 1 and single branch

git-clone-lite() {
	depth= d=1    # Clone depth
	single= s=    # Single branch
	branch= b=    # Branch to clone
	output= o=    # Output directory name

	eval "$(ally)"

	if [ $# -lt 1 ] || [ $# -gt 2 ]; then
		usage
	fi

	repo_url=$1 subdir=$2

	if [ -z "$output" ]; then
		output=$(basename "$repo_url")
	fi

	# Set up git clone arguments
	args=()
	if [ -n "$depth" ]; then
		args+=(--depth "$depth")
	fi
	if [ -n "$single" ]; then
		args+=(--single-branch)
	fi
	if [ -n "$branch" ]; then
		args+=(--branch "$branch")
	fi
	if [ -n "$subdir" ]; then
		args+=(--no-checkout)
	fi

	# Clone the repository
	git clone "${args[@]}" "$repo_url" "$output"

	# Sparse checkout for a specific subdirectory
	if [ -n "$subdir" ]; then
		cd "$output"
		git sparse-checkout init --cone
		git sparse-checkout set "$subdir"
		git checkout
	fi
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	git-clone-lite "$@"
fi

# version: 0.1.0
