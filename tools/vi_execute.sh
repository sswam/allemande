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
		lecho "#!/usr/bin/env python" "$name_comment_python" > "$A"
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
		lecho "#include <stdio.h>" "" "int main(int argc, char *argv[]) {" "	printf(\"Hello, world!\\n\");" "	return 0;" "}" > "$A"
		;;
	*.cpp)
		lecho "#include <iostream>" "" "int main(int argc, char *argv[]) {" "	std::cout << \"Hello, world!\" << std::endl;" "	return 0;" "}" > "$A"
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
