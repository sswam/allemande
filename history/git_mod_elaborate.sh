#!/bin/sh

# Version 0.0.1

show_staged=1
show_unstaged=1
show_untracked=1
show_ignored=0

while getopts "sadumit" opt; do
	case $opt in
		s) show_staged=1; show_unstaged=0; show_untracked=0 ;;
		a) show_staged=1; show_unstaged=1; show_untracked=1 ;;
		d) show_staged=0; show_unstaged=1; show_untracked=0 ;;
		u) show_staged=0; show_unstaged=0; show_untracked=1 ;;
		m) show_staged=0; show_unstaged=1; show_untracked=0 ;;
		i) show_ignored=1 ;;
		t) show_staged=1; show_unstaged=0; show_untracked=0 ;;
	esac
done

st=$(git status --short)

if [ $show_staged -eq 1 ]; then
	echo "$st" | grep '^[MADRC]' | sed -E 's/^[MADRC] //; s/^R  (.*) -> /\1\t/' | sortmtime -r | kut 2
fi

if [ $show_unstaged -eq 1 ]; then
	echo "$st" | grep '^ [MD]' | cut -c4- | sortmtime -r | kut 2
fi

if [ $show_untracked -eq 1 ]; then
	if [ $show_ignored -eq 1 ]; then
		echo "$st" | grep '^[?!]' | cut -c4- | sortmtime -r | kut 2
	else
		echo "$st" | grep '^?' | cut -c4- | sortmtime -r | kut 2
	fi
fi
