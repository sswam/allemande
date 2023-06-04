#!/bin/sh
# unhide-file: unhide a file by renaming it from a hidden file

exit=0
for file; do
	file=${file#.}
	dir=`dirname "$file"`
	base=`basename "$file"`
	hidden="$dir/.$base"
	if [ ! -e "$hidden" ]; then
		echo >&2 "$hidden" does not exist already
		exit=1
		continue
	fi
	if [ ! -h "$file" -o "`readlink "$file"`" != ".$base" ]; then
		echo >&2 "$file" is not a symlink to ".$base"
		exit=1
		continue
	fi
	rm "$file"
	mv "$hidden" "$file"
done
exit $exit
