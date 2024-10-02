#!/bin/bash
# [program ...]
# Lint a program

. each

lint_sh() {
	local prog="$1"
	local fail=0
	quiet shfmt "$prog" || fail=1
	quiet shellcheck -x "$prog" || fail=1
	return $fail
}

lint_py() {
	local prog="$1"
	fail=0
	quiet python3 -m py_compile "$prog" || fail=1
	quiet pylint --disable=all --enable=fixme "$prog" || fail=1
	quiet mypy "$prog" || fail=1
	return $fail
}

lint_c() {
	local prog="$1"
	fail=0
	quiet gcc -Wall -Wextra -Werror -fsyntax-only "$prog" || fail=1
	quiet clang -Wall -Wextra -Werror -fsyntax-only "$prog" || fail=1
	quiet clang-tidy "$prog" || fail=1
	quiet cppcheck "$prog" || fail=1
	quiet splint "$prog" || fail=1
	quiet flawfinder "$prog" || fail=1
	return $fail
}

lint_pl() {
	local prog="$1"
	fail=0
	quiet perl -Mstrict -cw "$prog" || fail=1
	quiet perlcritic "$prog" || fail=1
	return $fail
}

lint_go() {
	local prog="$1"
	fail=0
	quiet go vet "$prog" || fail=1
	quiet golint "$prog" || fail=1
	quiet staticcheck "$prog" || fail=1
	return $fail
}

lint_rs() {
	local prog="$1"
	fail=0
	quiet rustc --deny warnings "$prog" || fail=1
	quiet cargo clippy --all-targets --all-features -- -D warnings || fail=1
	return $fail
}

lint_js() {
	local prog="$1"
	fail=0
	quiet eslint "$prog" || fail=1
	quiet jshint "$prog" || fail=1
	quiet standard "$prog" || fail=1
	return $fail
}

lint_ts() {
	local prog="$1"
	fail=0
	quiet tsc --noEmit "$prog" || fail=1
	lint_js "$prog" || fail=1
	return $fail
}

linty() {
	local prog="$1"
	local ext="${prog##*.}"
	if [[ $prog != *.* ]]; then
		ext="sh"
	fi
	"lint_$ext" "$prog"
}

if [ "$BASH_SOURCE" == "$0" ]; then
	each linty : "$@"
fi
