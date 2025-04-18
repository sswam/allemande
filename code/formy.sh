#!/bin/bash
# [file ...]
# format source code files

. each

alias qs=quiet-on-success

formy() {
	local verbose= v=0	# verbose mode, output results when all tests pass

	eval "$(ally)"

	if (( $# != 1 )); then
		each formy : "$@"
		return $?
	fi

	(
		local prog="$(finder "$1")"
		if [ ! -f "$prog" ]; then
			echo >&2 "File not found: $1"
			return 1
		fi
#		cd "$(dirname "$prog")"
		local ext=${prog##*.}
		if [[ $prog != *.* ]]; then
			ext="sh"
		fi

		# handle Perl modules
		if [ "$ext" = pm ]; then
			ext=pl
		fi

		# avoid binary files
		if [[ $(file --mime-encoding -b "$prog") == "binary" ]]; then
			echo >&2 "Binary file, not formatting."
			return 0
		fi

		# call calls a function, but won't run a tool
		call "format_$ext" "$prog"
	)
}

run() {
	if (( verbose )); then
		verbose "$@"
	else
		qs verbose "$@" 2>/dev/null
	fi
}

# no-ops for some formats, for now
# TODO could maybe reformat, but nah

format_txt() { :; }
format_md() { :; }

format_html() {
	qs modify html-indent : "$1"
}

# TODO difference between svg / xml / html?

format_svg() {
	qs modify html-indent : "$1"
}

format_xml() {
	qs modify html-indent : "$1"
}

format_css() {
	qs css-beautify -r "$1"
	if [ -s "$1" ]; then
		echo >> "$1"
	fi
}

format_sh() {
	qs shfmt -w "$1"
}

format_py() {
	qs black --line-length 132 "$1"
}

format_c() {
	local style_file=$ALLEMANDE_HOME/c/clang-format-style
	qs clang-format -i -style=file:"$style_file" "$1"
}

format_pl() {
	qs perltidy -b "$1"
}

format_go() {
	qs gofmt -w "$1"
}

format_rs() {
	qs rustfmt "$1"
}

format_js() {
	qs prettier --write "$1"
}

format_ts() {
	format_js "$@"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	formy "$@"
fi
