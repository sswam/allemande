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

mp() {
	if [ -n "$(which mp)" ]; then
		command mp "$@"
	else
		mpv "$@"
	fi
}

case "${file,,}" in
*.txt|*.md|*.bb)
	less -- "$file" ;;
*.html|*.xhtml)
	chrome -- "$file" ;;
*.pdf)
	evince -- "$file" ;;
	# zathura "$file" ;;
*.png|*.jpg|*.jpeg|*.gif|*.bmp)
	qiv -D -X 0 -m -f -- "$file" ;;
	# sxiv "$file" ;;
*.mp4|*.mkv|*.avi|*.webm|*.mpg|*.mpeg|*.m4v|*.ts|*.flv|*.wmv)
	mp -- "$file" ;;
*.mp3|*.ogg|*.wav|*.aac)
	mp -- "$file" ;;
*.zip)
	mcomix -- "$file" ;;
*)
	ls -l -- "$file" ;;
esac
