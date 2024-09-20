#!/bin/bash -eu
# [<input.html|-> [<url>]]
# Convert HTML to Markdown, as cleanly as possible.

pandoc-dump() {
	c=1	# clean
	m=1	# metadata

	. opts

	local old_opts=$(set +o)
	set -eu

	html="${1:--}"
	url="${2:-}"

	# if $html = -, save stdin to a temp file and use that
	temp=
	if [ "$html" = "-" ]; then
		html=`mktemp`
		cat > "$html"
		temp=1
	fi

	if [ "$m" = 1 ]; then
		show_metadata
	fi

	if [ "$c" = 1 ]; then
		< "$html" htmlsplit | htmldebloater | pandoc-dump-clean-html | pandoc_convert | clean
	else
		< "$html" htmlsplit | htmldebloater | pandoc_convert
	fi

	if [ -n "$temp" ]; then
		rm "$html"
	fi

	eval "$old_opts"
}

pandoc_convert() {
	pandoc --wrap=none -f html -t markdown
}

clean() {
	pandoc-dump-clean |
	single-blank-lines.pl
#	pandoc-dump-clean-2
}

show_metadata() {
	local title=`html-title < "$html"`
	printf "title: %s\n" "$title"
	if [ -n "$url" ]; then
		printf "From: %s\n" "$url"
	fi
	echo
}

if [ "$BASH_SOURCE" = "$0" ]; then
	pandoc-dump "$@"
fi
