#!/bin/bash -eu
# [source_paths...] [target_dir]
# Create symlinks for executable files and .sh files in the canon directory

canon() {
	local v=0    # verbose mode
	local f=0    # force overwrite existing symlinks
	local d=0    # dry run mode
	local D=canon   # target directory

	. opts

	local target_dir="$D"
	local sources=("$@")

	mkdir -p "$target_dir"

	for source in "${sources[@]}"; do
		if [ -d "$source" ]; then
			canon_process_dir "$source" "$target_dir"
		elif [ -f "$source" ]; then
			create_symlink "$source" "$target_dir"
		else
			echo "Warning: Invalid source: $source" >&2
		fi
	done
}

canon_process_dir() {
	find "$source" -maxdepth 1 -type f \( -executable -o -name "*.sh" \) |
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
	ln -sf "$relative_path" "$symlink_path"
}

if [ "$BASH_SOURCE" = "$0" ]; then
	canon "$@"
fi
