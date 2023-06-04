#!/bin/bash -eu
# sl_gify: convert a string to a slug

# It turns out that there is a slugify in PyPI also; I should probably use that instead.
# But I need this one for a project at the moment. I'll rename it to sl_gify for now.

sl_gify_filter() {
	sed 's/[^a-zA-Z0-9]/_/g; s/__*/_/g; s/^_//; s/_$//'
}

sl_gify() {
	if [ -n "$*" ]; then
		printf "%s\n" "$*" | sl_gify_filter
	else
		sl_gify_filter
	fi
}

if [ "$0" = "$BASH_SOURCE" ]; then
	exec=exec
	v "$@"
fi
