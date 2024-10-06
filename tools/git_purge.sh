#!/bin/bash -eu
# git-purge:	Remove files from git history

echo >&2 "NOT TESTED YET, BE CAREFUL!"
exit 1

repo=$1
shift
exclude=( "$@" )

# 1. clone the repo local to local
repo_abs=$(readlink -f "$repo")
tmp=$(mktemp -d)
cd "$tmp"

git clone --no-local "$repo_abs" .

# 2. remove the files from all commits
path_args=()
for path in "${exclude[@]}"; do
	path_args+=( --path "$path" )
done

git filter-repo --invert-paths "${path_args[@]}"

# 3. compare the modified repo working copy to the new one
diff -ru "$repo_abs" . | sed -e "s|$tmp/||" | colordiff
