#!/bin/bash -eu
# slugify: convert a string to a slug

# It turns out that there is a slugify in PyPI also; I should probably use that instead.
# But I need this one for a project at the moment. I'll rename it to sl_gify for now.

# TODO kebab case, etc.
# TODO efficient proc, i.e. don't use cat

u=	# uppercase (default is mixed)
l=	# lowercase (default is mixed)
H=	# use hyphens instead of underscores

. opts

uppercase=$u
lowercase=$l
hyphen=$H

slugify_filter() {
	sed 's/[^a-zA-Z0-9]/_/g; s/__*/_/g; s/^_//; s/_$//'
}

slugify() {
	local proc=cat
	local proc2=cat

	if [ "$uppercase" = 1 ]; then
		proc=uc
	elif [ "$lowercase" = 1 ]; then
		proc=lc
	fi

	if [ "$hyphen" = 1 ]; then
		proc2="tr _ -"
	fi

	if [ -n "$*" ]; then
		printf "%s\n" "$*" | slugify_filter
	else
		slugify_filter
	fi | $proc | $proc2
}

if [ "$0" = "$BASH_SOURCE" ]; then
	slugify "$@"
fi
