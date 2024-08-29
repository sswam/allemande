#!/bin/bash -eu
m=$ALLEMANDE_LLM_DEFAULT
. opts
while read module; do
	echo >&2 "Processing $module"
	(
		echo "## $module"
		echo
		< "$module.nls" perl -ne 'print "$1\n" if /^\s*to ([\w-]+)/' |
		while read func; do
			cat "$module/$func.nls.md"
		done
	) > "$module/all-ordered.md"
	if [ ! -e "$module/summary.md" ]; then
		< "$module/all-ordered.md" v llm process -m $m "Please give a short overview summary of this \`$module\` module:" > "$module/summary.md"
	fi
	(
		echo "## $module"
		echo
		cat "$module/summary.md"
		echo
		echo
		< "$module.nls" perl -ne 'print "$1\n" if /^\s*to ([\w-]+)/' |
		while read func; do
			cat "$module/$func.nls.md"
		done
		echo '\newpage'
		echo
	) > "$module/all-ordered-with-summary.md"
	cat "$module/all-ordered-with-summary.md"
done < module-order.txt > doc.md
pandoc doc.md -o doc.pdf
