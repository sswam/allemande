#!/bin/bash -eu
# 
# Interactive git add with diffs, and llm-git-commit

git_diff_interactive() {
	local X=0	# no xterm
	local C=10	# diff context
	local files_relative=("$@")	# relative to cwd

	. opts
	. confirm

	setup_actions

	files=()
	added=()
	git_root=$(git-root)

	resolve_files "${files_relative[@]}"
	cd "$git_root"

	local IFS=$'\n'
	local modified=($(git-mod "${files[@]}"))
	for file in "${modified[@]}"; do
		action_diff "$file" || true
		process_file "$file"
	done
}

setup_actions() {
	actions="
	c	commit
	a	add
	t	touch
	R	remove
	I	ignore
	n	next
	q	next
	C	commit previous
	d	diff
	v	view
	e	edit
	S	snip
	X	exit
	?	help
	"

	declare -g -A action_names

	action_keys=""

	while read -r key name; do
		if [ -z "$key" ]; then
			continue
		fi
		action_keys+=$key
		action_names[$key]=${name// /_}
	done < <(echo "$actions")
}

resolve_files() {
	prefix=$(git rev-parse --show-prefix)

	for file in "${files_relative[@]}"; do
		file+=("$prefix$file")
		file=$(realpath "$file")
		file=${file#$git_root/}
		files+=("$file")
	done
}

process_file() {
	local file=$1
	local IFS=$'\n'
	while true; do
		if [ "${#added[@]}" -gt 0 ]; then
			echo "[${added[*]}]"
			echo
		fi
		read -n1 -p "Action? [$action_keys]: " key
		echo

		if [ -z "$key" ]; then
			key=-
		fi

		if [[ ! "$action_keys" =~ "$key" ]]; then
			echo >&2 "Invalid choice"
			echo
			continue
		fi

		action=${action_names[$key]}

		action_func=action_$action
		if $action_func "$file"; then
			break
		fi
	done
}

action_commit() {
	local file=$1
	added+=("$file")
	action_commit_previous
	return 0
}

action_add() {
	local file=$1
	added+=("$file")
	return 0
}

action_touch() {
	local file=$1
	touch --no-dereference "$file"
	return 0
}

action_remove() {
	local file=$1
	move-rubbish "$file"
	return 0
}

action_ignore() {
	local file=$1
	printf "/%s\n" "$file" >> "$git_root/.gitignore"
	return 0
}

action_next() {
	return 0
}

action_commit_previous() {
	local IFS=$'\n'
	if ((X)); then
		llm-git-commit "${added[@]}"
	else
		setsid xterm -title "ci ${added[*]}" -e llm-git-commit "${added[@]}" &
	fi 
	added=()
	return 1
}

action_diff() {
	local file=$1
	clear
	git status -s "$file"
	echo
	if git ls-files --error-unmatch "$file" >/dev/null 2>&1; then
		git diff -U$C --color "$file"
	else
		action_view "$file" || true
	fi
	echo
	return 1
}

action_view() {
	local file=$1
	if [ -d "$file" ]; then
		ls --color -d "$file"
		echo
		ls --color "$file"
	elif [ -L "$file" ]; then
		echo "$file -> $(readlink "$file")"
	elif [ -f "$file" ]; then
		batcat --style header,grid,changes --tabs=8 "$file"
	else
		ls --color -l "$file"
	fi
	return 1
}

action_edit() {
	local file=$1
	$EDITOR "$file"
	return 1
}

action_snip() {
	local file=$1
	local snip="$(git-root)/snip"
	mkdir -p "$snip"
	mv -iv "$file" "$snip"

	# add /snip to .gitignore if not already there and not commented out
	if ! grep -q -E "^(# *)?/snip$" .gitignore; then
		echo "/snip" >> .gitignore
	fi
	return 1
}

action_exit() {
	exit
}

action_help() {
	echo "$actions"
	return 1
}

if [ "$BASH_SOURCE" = "$0" ]; then
	git_diff_interactive "$@"
fi
