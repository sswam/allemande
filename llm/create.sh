#!/bin/bash
# [file] "instructions to create it" [reference files ...]
# Write something using AI

create() {
	local m=	# model
	local s=1	# refer to hello.<ext> for style
	local e=1	# edit

	. opts

	# strict mode
	local old_opts=$(set +o)
	set -e -u -o pipefail
	trap 'eval "$old_opts"' RETURN

	local file=$1
	local prompt=${2:-}
	shift 2 || shift 1 || true
	local refs=("$@")

	# Check if file already exists
	if [ -e "$file" ]; then
		echo >&2 "already exists: $file"
		exit 1
	fi

	local dir=$(dirname "$file")
	local base=$(basename "$file")

	local ext=${base##*.}
	if [ "$ext" == "$base" ]; then
		ext="sh"
	fi

	# style reference and prompt for -s option
	style="hello_$ext.$ext"
	if [ "$s" = 1 -a -n "$(wich "$style")" ]; then
		refs+=("$style")
		prompt="in the style of \`$style\`, $prompt"
	fi

	mkdir -p "$dir"

	prompt="Please write \`$base\`, $prompt"

	local input=$(cat_named.py -p -b "${refs[@]}")

	if [ -z "$input" ]; then
		input=":)"
	fi

	comment_char="#"
	case "$ext" in
	c|cpp|java|js|ts|php|cs|go|rs|swift|kt|scala|groovy|dart|fs|v|nim|zig|vala|cr|wren|d|odin|jai|pony|haxe)
		comment_char="//"
		;;
	sh|py|pl|rb|lua|tcl|awk|sed|bash|zsh|fish|ps1|psm1|psd1|r|jl|crystal|elixir|ex|exs|ml|mli|coffee|haskell|hs|nim)
		comment_char="#"
		;;
	md|txt|html|xml|json|yaml|yml|toml|ini|conf|cfg|properties|env|csv|tsv|rec|log|sql)
		comment_char=""
		;;
	lisp|clj|scm|rkt)
		comment_char=";"
		;;
	f|f90|f95|f03|f08)
		comment_char="!"
		;;
	vim)
		comment_char='"'
		;;
	esac

	# Process input and save result
	printf "%s\n" -- "$input" | process -m="$m" "$prompt" |
	if [ -n "$comment_char" ]; then
		markdown_code.py -c "$comment_char"
	else
		cat
	fi > "$file"

	if [ -n "$comment_char" ]; then
		chmod +x "$file"
	fi

	if (( "$e" )); then
		$EDITOR "$file"
	fi
}

if [ "$BASH_SOURCE" = "$0" ]; then
	create "$@"
fi
