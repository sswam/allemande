#!/bin/sh
# hide-file: hide a file by renaming it to a hidden file

exit=0
for file; do
	file="${file%/}"
	dir=`dirname "$file"`
	base=`basename "$file"`
	hidden="$dir/.$base"
	if [ -e "$hidden" -a -h "$file" -a "`readlink "$file"`" = ".$base" ]; then
		# already good
		continue
	fi
#	if [ -e "$hidden" ]; then
#		echo >&2 "$hidden" exists already
#		exit=1
#		continue
#	fi
	if [ ! -e "$file" ]; then
		echo >&2 "$file" does not exist
		exit=1
		continue
	fi
	if [ -d "$hidden" ]; then
		echo >&2 "$hidden" already exists, and is a directory
		exit=1
		continue
	fi
	mv "$file" "$hidden"
	ln -s ".$base" "$file"
done
exit $exit
