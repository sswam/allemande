#!/bin/bash -eu
# file
# open a file in a sensible application for viewing, preferably on the terminal
# used by `curate` script
# TODO write a similar editor script for editing files

file="$1"

if [ -d "$file" ]; then
	# shellcheck disable=SC2012
	ls --color "$file" | less -R
	exit
fi

case "$file" in
*.txt|*.md|*.bb)
	less "$file" ;;
*.html|*.xhtml)
	chrome "$file" ;;
*.pdf)
	evince "$file" ;;
	# zathura "$file" ;;
*.png|*.jpg|*.jpeg|*.gif|*.bmp)
	qiv "$file" ;;
	# sxiv "$file" ;;
*.mp4|*.mkv|*.avi|*.webm|*.mpg|*.mpeg|*.m4v|*.ts)
	mpv -- "$file" ;;
*.mp3|*.ogg|*.wav|*.aac)
	mpv -- "$file" ;;
*.zip)
	mcomix -- "$file" ;;
*)
	ls -l "$file" ;;
esac
