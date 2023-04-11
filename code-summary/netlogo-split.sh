#!/bin/bash -eu

# netlogo-split-and-tsort.sh:
# Split NetLogo files into separate files for each procedure.

# TODO: This is a hack.  It should be rewritten in Python.

# for file in *.nls *.nlogo; do
for file in `<fixme.txt`; do
	base=${file%.*}
	if [ -d "$base" ]; then
		echo "Skipping $file"
		continue
	fi
	mkdir "$base"
	< "$file" split-file -r -d '\nto' -i start
	mv stdin-* "$base"
	(
		i=0
		cd "$base"
		for splitfile in stdin-*; do
			name=`< "$splitfile" perl -ne '
				if (/^\s*to ([\w-]+)/) {
					print "$1\n";
					exit;
				}
			'`
			if [ -z "$name" ]; then
				name=unknown-$i
				i=$((i+1))
			fi
			mv -iv "$splitfile" "$name.nls"
		done
	)
done
