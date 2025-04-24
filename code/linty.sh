#!/bin/bash
# [program ...]
# Lint a program

. each

linty() {
	local verbose= v=0	# verbose mode, output results when all tests pass
	local unique= u=0        # strip line numbers and de-duplicate messages

	eval "$(ally)"

	if (( $# != 1 )); then
		each linty : "$@"
		return $?
	fi

	(
		local prog="$(finder "$1")"
		if [ ! -f "$prog" ]; then
			echo >&2 "File not found: $1"
			return 1
		fi
#		cd "$(dirname "$prog")"
		base="$(basename "$prog")"
		local ext="${base##*.}"
		if [[ $base != *.* ]] && [ "$base" != Makefile ]; then
			ext="sh"
		fi

		# handle Perl modules
		if [ "$ext" = pm ]; then
			ext=pl
		fi

		# avoid binary files
		if [[ $(file --mime-encoding -b "$prog") == "binary" ]]; then
			echo >&2 "Binary file, not linting."
			return 0
		fi

		local output_file="$prog.lint"

		# call calls a function, but won't run a tool
		# dedup and save in any case, but output what the user asked for
		if ((unique)); then
			exec 3>/dev/null 4>&1
		else
			exec 3>&1 4>/dev/null
		fi
		call "lint_$ext" "$prog" 2>&1 |
			tee "$output_file" /dev/fd/3 |
			dedup | tee "$output_file.dedup" >&4
		exec 3>&- 4>&-
	)
}

dedup() {
	perl -pe 's/.*?:(\d+:)+ *//' | uniqo
}

run() {
	if (( verbose )); then
		v+ "$@"
	else
		quiet-on-success v+ "$@" 2>/dev/null
	fi
}

# no-ops for some formats, for now
# TODO could check markdown, could maybe spell-check text!

lint_txt() { :; }
lint_md() { :; }
lint_html() { :; }

lint_sh() {
	local prog="$1"
	local fail=0
	run shfmt "$prog" || fail=1
	run shellcheck -x "$prog" || fail=1
	return $fail
}

lint_py() {
	local prog="$1"
	fail=0
	run python3 -m py_compile "$prog" || fail=1
	run pylint "$prog" || fail=1
	run mypy "$prog" || fail=1
	return $fail
}

lint_c() {
	local prog="$1"
	fail=0
	run cc -Wall -Wextra -Werror -fsyntax-only $CFLAGS "$prog" $LDFLAGS || fail=1
# 	run clang-tidy "$prog" || fail=1
# 	run cppcheck "$prog" || fail=1
# 	run splint +posixlib "$prog" || fail=1
# 	run flawfinder "$prog" || fail=1
	return $fail
}

perl_c_fail_on_output() {
	! "$@" 2>&1 | grep -v ' syntax OK$'
}

lint_pl() {
	local prog="$1"
	fail=0
	perl_c_fail_on_output perl -Mstrict -cw "$prog" || fail=1
	run perlcritic "$prog" || fail=1
	return $fail
}

lint_go() {
	local prog="$1"
	fail=0
	run go vet "$prog" || fail=1
	run golint "$prog" || fail=1
	run staticcheck "$prog" || fail=1
	return $fail
}

lint_rs() {
	local prog="$1"
	fail=0
	# run rustc --deny warnings "$prog" || fail=1
	run cargo clippy --all-targets --all-features -- -D warnings || fail=1
	return $fail
}

lint_js() {
	local prog="$1"
	fail=0
	run eslint "$prog" || fail=1
	return $fail
}

lint_ts() {
	local prog="$1"
	fail=0
	run tsc --noEmit "$prog" || fail=1
	lint_js "$prog" || fail=1
	return $fail
}

lint_css() {
	local prog="$1"
	fail=0
	run stylelint "$prog" || fail=1
	return $fail
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	linty "$@"
fi
