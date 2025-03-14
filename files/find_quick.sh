#!/bin/bash -e
# find-quick: find files quickly, excluding some large directories,
# where I don't put anything I need to find quickly.

# options before -- are for find, after -- are for grep
# if we have no --, the options are for grep

# Usage: f [gre-opts]
#        f [find-opts] -- [grep-opts]
#        f dir [find-opts] -- [grep-opts]


FIND_OPTS=()
GREP_OPTS=()
sep=0
for arg; do
	if [ "$arg" = '--' ]; then
		sep=1
		shift
		break
	fi
	FIND_OPTS+=("$arg")
	shift
done
GREP_OPTS=("$@")

# If we have no sep, in fact the FIND_OPTS are GREP_OPTS
if [ "$sep" = 0 ]; then
	GREP_OPTS=("${FIND_OPTS[@]}")
	FIND_OPTS=()
fi

# add -print only if FIND_OPTS do not contain print / printf
FIND_OPTS_S="${FIND_OPTS[*]}"
# check for whole words
if [[ "$FIND_OPTS_S" != *-printf* ]]; then
	FIND_OPTS+=(-printf '%p\n')
fi

# if first of FIND_OPTS starts with -, then it's not a dir
dir=.
if [ "${#FIND_OPTS[@]}" -gt 0 -a "${FIND_OPTS[0]:0:1}" != '-' ]; then
	dir="${FIND_OPTS[0]}"
	# remove first FIND_OPTS
	FIND_OPTS=("${FIND_OPTS[@]:1}")
fi

do_find() { 
	find "$dir" \( \
		-name '..' \
		-o -name '.?*' \
		-o -name 'sparkjoy' \
		-o -name 'node_modules' \
		-o -name 'soft' \
		-o -name 'tmp' \
		-o -name 'rubbish' \
		-o -name '__pycache__' \
		-o -name 'venv' \
		-o -name 'soft-ai' \
		-o -name 'Z' \
		-o -name 'ff' \
		-o -name 'webssh2' \
		-o -name 'arwen' \
		-o -name 'gandalf' \
		-o -name 'beorn' \
		-o -path '*/www/word' \
		-o -path '*/sam-new/vim' \
		-o -path '*/ai/data' \
		-o -name 'rooms.server' \
		\) -prune -o "${FIND_OPTS[@]}"
}

do_type() {
	perl -ne 'chomp; print; -d $_ and print "/"; print "\n"'
}

do_grep() {
	grep "${GREP_OPTS[@]}"
}

# if we have GREP_OPTS, do grep, else do type
if [ "${#GREP_OPTS[@]}" -gt 0 ]; then
	do_find | do_type | do_grep
else
	do_find | do_type
fi
