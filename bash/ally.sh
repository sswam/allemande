#/usr/bin/env bash
# Eval this script: eval "$(ally)"

# output the contents of the script after this
exec < "$BASH_SOURCE" tail -n +7 || exit 1

# strict mode
local old_opts 2>/dev/null
old_opts=$(set +o)
set -e -u -o pipefail
trap 'eval "$old_opts"' RETURN

shopt -s expand_aliases

. opts
eval "$(opts_long.py "$0")"
. each

quote_command() {
	local cmd=$(printf "%q " "$@")
	cmd=${cmd% }
	printf "%s\n" "$cmd"
}

alias qc=quote_command
alias X=eval

ret() {
	qc "$@"
	echo 'return $?'
}

tryit() {
	X $(ret ls /)
}

backup() {
	local file=$1
	if [ -e "$file~" ]; then
		move-rubbish "$file~"
	fi
	yes n | cp -i -a "$file" "$file~" || true
}

locate_file() {
	local file=$1
	if [ ! -e "$file" ]; then
		local file2=`wich $file`
		if [ ! -e "$file2" ]; then
			echo >&2 "not found: $file"
			return 1
		fi
		file=$file2
	fi
	file=$(readlink -e "$file")
	echo "$file"
}

code_modify() {
	local E=0	# do not edit

	. opts

	local file=$1
	shift
	local command=( "$@" )

	# If no file is provided, process input stream
	if [ -z "$file" -o "$file" = "-" ]; then
		"${command[@]}" | markdown_code.py -c '#'
		return
	fi

	# Locate the file and create a backup
	file=$(locate_file "$file")
	[ -n "$file" ] || return 1
	backup "$file"

	# Process the file content and save to a temporary file
	< "$file" "${command[@]}" | markdown_code.py -c '#' > "$file~"

	# Swap the original and processed files
	swapfiles "$file" "$file~"

	# Open both files in vimdiff for comparison
	if [ "$E" = 0 ]; then
		vimdiff "$file" "$file~"
	fi
}

die() {
	printf >&2 "%s: fatal: %s\n" "${0##*/}" "$*"
	exit 1
}

notify() {
	local name="${0##*/}"
	name=${name%.*}
	notify-send -u critical -t 10000 \
		-i /usr/share/icons/gnome/48x48/status/appointment-soon.png \
		"$name" "$1"
}

countdown() {
	local remaining=$1 warn=$2
	shift 2
	while [ $remaining -gt 0 ]; do
		if [ $remaining -le $warn ]; then
			notify "$remaining seconds"
		fi
		sleep 1
		remaining=$((remaining - 1))
	done
}

countdown_wrap() {
	local timeout=$1 warn=$2
	shift 2
	if (( timeout )); then
		countdown $timeout $warn &
		countdown_pid=$!
		old_opts=$(set +o)
		ret=1
		set +e
		"$@"
		ret=$?
		kill $countdown_pid 2>/dev/null
		eval "$old_opts"
		return $ret
	else
		"$@"
	fi
	stty sane
	return "$ret"
}
