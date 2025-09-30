#!/usr/bin/env bash

# Adds version numbers to files based on their git commit count
# Sets version as 0.1.N where N is the commit count

version-add() {
	local file="$1"
	if [ ! -f "$file" ]; then
		printf >&2 "%s: not a regular file\n" "$file"
		return 1
	fi

	local count=1 minor version
	count=$(time git rev-list --count HEAD -- "$file") || true
	minor=$((${count:-1} - 1))
	if [ "$minor" -lt 0 ]; then
		minor=0
	fi
	version="0.1.$minor"

	if [ "$dry_run" = 1 ]; then
		printf "%s\t%s\n" "$file" "$version"
		return 0
	fi

	case "$file" in
	*.py)
		sed -i "1{/^#!/h;x;s/.*/__version__ = '$version'/;G;}" "$file"
		;;
	*.pl)
		sed -i "1{/^#!/h;x;s/.*/our \$VERSION = '$version';/;G;}" "$file"
		;;
	*.go)
		sed -i "1{/^package/h;x;s/.*/const Version = \"$version\"/;G;}" "$file"
		;;
	*.rs)
		sed -i "1i pub const VERSION: &str = \"$version\";" "$file"
		;;
	*.c|*.h|*.cc|*.js)
		sed -i "1i// version: $version" "$file"
		;;
	*.html|*.css)
		sed -i "1i<!-- version: $version -->" "$file"
		;;
	*.wasm)
		sed -i "1i;; version: $version" "$file"
		;;
	*.md)
		sed -i "1i[//]: # (version: $version)" "$file"
		;;
	# *.txt)
	# 	sed -i "1,/^$/!b;/^$/a\\$version\\n" "$file"
	# 	;;
	*.sh|*.make|*.txt|*)
		printf "\n# version: %s\n" "$version" >> "$file"
		;;
	esac
}

version-add-many() {
	local dry_run= n=  # dry run mode

	eval "$(ally)"

	local file
	for file; do
		version-add "$file"
	done
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	version-add-many "$@"
fi

# version: 0.1.0
