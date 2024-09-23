#!/bin/bash -eu
# [source_paths...] [target_dir]
# Create symlinks in the canon directory for executable files and .sh files

canon() {
	local v=0    # verbose mode
	local f=0    # force overwrite existing symlinks
	local d=0    # dry run mode
	local D=canon   # target directory

	. "$ALLEMANDE_HOME/bash/opts.sh"

	local target_dir="$D"
	local sources=("$@")

	mkdir -p "$target_dir"

	for source in "${sources[@]}"; do
		canon_process_path "$source" "$target_dir"
	done
}

canon_process_path() {
	# skip hidden files and directories; skip foo.bar.bak and similar with two dots;
	# match executable files and .sh files
	find "$source" -maxdepth 1 -not -path '*/.*' -not -path '*/*.*.*' -type f \( -executable -o -name "*.sh" \) |
	while read -r file; do
		create_symlink "$file" "$target_dir"
	done
}

create_symlink() {
	local file="$1"
	local target_dir="$2"
	local filename=$(basename "$file")
	local stem=${filename%.*}  # Remove file extension
	local symlink_name=${stem//_/-}  # Replace underscores with dashes

	local relative_path=$(realpath --relative-to="$target_dir" "$file")
	local symlink_path="$target_dir/$symlink_name"

	if [ "$v" = 1 -o "$d" = 1 ]; then
		echo "$symlink_path	$relative_path"
	fi
	if [ "$d" = 1 ]; then
		return
	fi

	different_symlink=0
	if [ -L "$symlink_path" -a "$(readlink "$symlink_path")" != "$relative_path" ]; then
		different_symlink=1
		echo >&2 "replacing symlink: $(readlink "$symlink_path") -> $relative_path"
	fi
	if [ ! -L "$symlink_path" -o "$different_symlink" = 1 ]; then
		ln -sf "$relative_path" "$symlink_path"
	fi
}

if [ "$BASH_SOURCE" = "$0" ]; then
	canon "$@"
fi
