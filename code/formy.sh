#!/bin/bash
# [file ...]
# format source code files

. each

formy() {
	local verbose= v=0	# verbose mode, output results when all tests pass

	eval "$(ally)"

	if (( $# != 1 )); then
		each formy : "$@"
		return $?
	fi

	(
		local prog="$(finder "$1")"
		cd "$(dirname "$prog")"
		local ext=${prog##*.}
		if [[ $prog != *.* ]]; then
			ext="sh"
		fi
		"format_$ext" "$prog"  # beware of the hdd extension!
	)
}

run() {
	if (( verbose )); then
		v "$@"
	else
		v quiet "$@" 2>/dev/null
	fi
}

format_sh() {
	quiet shfmt -w "$1"
}

format_py() {
	quiet black --line-length 100 "$1"
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

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	formy "$@"
fi
