# Eval this script: eval "$(<$(W ally))"
# It's hacky but magickal!

# strict mode
local old_opts=$(set +o)
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
