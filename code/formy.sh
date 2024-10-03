#!/bin/bash
# [file ...]
# format source code files

formy() {
	eval "$(ally)"

	[ "$#" = 1 ] || each formy : "$@"

	local prog="$1"
	local ext=${prog##*.}
	if [[ $prog != *.* ]]; then
		ext="sh"
	fi
	"format_$ext" "$prog"  # beware of the hdd extension!
}

format_sh() {
	quiet shfmt -w "$1"
}

format_py() {
	quiet black "$1"
}

format_c() {
	quiet clang-format -i "$1"
}

format_pl() {
	quiet perltidy -b "$1"
}

format_go() {
	quiet gofmt -w "$1"
}

format_rs() {
	quiet rustfmt "$1"
}

format_js() {
	quiet prettier --write "$1"
}

format_ts() {
	format_js "$@"
}

if [ "$BASH_SOURCE" == "$0" ]; then
	formy "$@"
fi
