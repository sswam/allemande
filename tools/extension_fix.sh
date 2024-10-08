#!/bin/bash -eu
# extension-fix	Fix file extensions based on mime type

a=	# append the new extension to the old one
v=	# verbose
o=y	# overwrite existing files: y/n
m=/etc/mime.types	# mime types file
E=	# do not echo before and after filenames

. opts

append=$a
verbose=$v
overwrite=$o
mime_types=$m

if [ "$verbose" = 1 ]; then
	verbose=v
else
	verbose=
fi

files_exist=()
for file; do
	if [ -e "$file" ]; then
		files_exist+=("$file")
	else
		echo >&2 "WARNING: $file does not exist"
	fi
done

# if none exist, exit
if [ ${#files_exist[@]} -eq 0 ]; then
	exit 0
fi

(
	techo file mimetype
	file -i --separator $'\t' -- "${files_exist[@]}"
) |
process-tsv -m '$mimetype =~ s/^\s+|;.*|\s+$//g' |
tail -n +2 | (
	IFS=$'\t'
	while read file mimetype; do
		ext_old=${file##*.}
		entry=`look "$mimetype"$'\t' "$mime_types" || grep "^$mimetype" "$mime_types" | head -n 1 || true`
		if [ "$entry" == "text/xml" ]; then
			entry="xml"
		fi
		ext=`echo "$entry" | sed 's/.*\t//' | cut -f1 -d ' '`
		if [ -n "$ext" -a "$ext" != "$ext_old" ]; then
			if [ "$a" = 1 ]; then
				ext="$ext_old.$ext"
			fi
			dest="${file%.*}.$ext"
			yes "$overwrite" | mv -i$verbose "$file" "$dest"
			if [ ! -e "$file" ]; then
				techo "$file" "$dest"
			fi
		elif [ -z "$entry" ]; then
			echo >&2 "WARNING: No entry for $mimetype in $mime_types"
		elif [ -z "$ext" ]; then
			echo >&2 "WARNING: No extension for $mimetype, old extension was $ext_old"
		fi
	done
)
