#!/bin/bash
# vx:	vi wrapper to create executable files if they don't exist
for A; do
	if [ ! -s "$A" ]; then
		touch "$A"
	fi
	chmod +x "$A"
	if [ -s "$A" ]; then
		continue
	fi
	name="$(basename "$A")"
	name_comment="# $name:	"
	name_comment_slashes="// $name:	"
	name_comment_python="\"\"\" $name:	\"\"\""
	case "$A" in
	*.py)
		< ~/code/python/hello.py sed -e 's/hello.py/'"$name"'/' > "$A"
		;;
	*.pl)
		lecho "#!/usr/bin/perl -w" "$name_comment" "use strict;" "use warnings;" "" > "$A"
		;;
	*.js)
		lecho "#!/usr/bin/env node" "$name_comment_slashes" > "$A"
		;;
	*.rb)
		lecho "#!/usr/bin/env ruby" "$name_comment" > "$A"
		;;
	*.lua)
		lecho "#!/usr/bin/env lua" "$name_comment" > "$A"
		;;
	*.txt|*.md)
		;;
	*.make)
		lecho "#!/usr/bin/make -f" "$name_comment" > "$A"
		;;
	*.c)
		< ~/code/c/hello.c sed -e 's/hello.c/'"$name"'/' > "$A"
		;;
	*.cpp)
		< ~/code/c/hello.cpp sed -e 's/hello.cpp/'"$name"'/' > "$A"
		;;
	*)
		lecho "#!/bin/bash -eu" "$name_comment" > "$A"
		;;
	esac
done
${VXED:-vi -o} "$@"
for A; do
	if [ ! -s "$A" ]; then
		rm -f "$A"
	fi
done
