#!/bin/bash -eu

# llm-last:		show recent llm generation/s from ~/llm.log
# llm-last		shows the most recent
# llm-last 3 1		shows 3rd most recent and most recent
#	Even numbered are prompts, odd numbered are AI responses.

f=0	# output filenames, not content
c=0	# output code, using markdown_code -c '#' (or provided prefix)
m=	# view markdown in Chrome with Markdown Viewer
e=0	# edit

. opts

# no editing and chroming together
if [ "$e" = 1 -a "$m" = 1 ]; then
	echo >&2 "Can't edit and view in Chrome at the same time."
	exit 1
fi

# default to # comments
if [ "$c" = 1 ]; then
	c='#'
fi

cd ~/llm.log

llm_last() {
	for i in "${@:-1}"; do
		ls1 -n="$i"
	done
}

if [ "$f" = 1 ]; then
	llm_last "$@"
elif [ "$m" = 1 ]; then
	llm_last "$@" | xa chrome
elif [ "$c" != 0 ]; then
	llm_last "$@" | xa catpg | markdown_code.py -c "$c"
else
	llm_last "$@" | xa catpg
fi | if [ "$e" = 1 ]; then
	vipe
else
	less
fi
