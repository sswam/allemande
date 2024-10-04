#!/bin/sh

# sed-escape


# The metacharacters

meta_chars='][\.*^$\/\\&'  # . / and \ are escaped, else sed breaks
extended_chars="+?|(){}"

usage() {
	if ! command -v basename >/dev/null 2>&1; then
		name=$(basename "$0")
	else
		name="sed-escape"
	fi
	echo "$name version 1.0.0"
	echo
	echo "Usage: $name [-E|--extended] [-x extras] [-i | -- text]"
	echo
	echo "Options:"
	echo "  -E, --extended  Escape for extended regular expressions."
	echo "  -i              Escape every line of stdin."
	echo "  -x extras       Escape the characters in extras."
	echo "  --              Separate options from the text (mandatory)"
	echo "  -h, --help      Display this help message."
	echo
	echo "This program escapes all metacharacters in the input text,"
	echo "for use in sed regular patterns or replacement strings."
	echo "It also escapes any characters in the extras string."
	echo "The output is written to stdout."
	echo
	echo "Examples:"
	echo
	echo "  $name -- 'a*b' 'c[d]'"
	echo "  $name -E -- 'a*b' 'c{d}'"
	echo "  $name -x '!%' -- 'a%b' 'c[d]'"
	echo "  echo 'a*b' | $name -i"
	echo
}

extended=0  # escape for sed ERE regular expressions.
stdin=0     # escape every line of stdin

while [ $# -gt 0 ]; do
	case "$1" in
	-E|--extended)
		extended=1
	       	shift
		;;
	-i)
		stdin=1
		shift
		;;
	-x)
		shift
		extras="$1"
		shift
		;;
	-h|--help)
		usage
		exit 0
		;;
	--)
		break
		;;
	-*)
		echo "Unknown option: $1" >&2
		usage >&2
		exit 1
		;;
	*)
		break
		;;
	esac
done

sed_escape() {
	text="$1"

	if ! command -v sed >/dev/null 2>&1; then
		echo "sed not found." >&2
		exit 1
	fi

	# Escape the text, and also replace newlines with \n
	printf '%s\n' "$text" |
		sed "s/[$meta_chars]/\\\\&/g;" |
		sed ':a;N;$!ba;s/\n/\\n/g'
}

process_arguments() {
	if [ $# -eq 0 ] || [ "$1" != "--" ]; then
		echo "You must use -- to separate options from the text." >&2
		usage >&2
		exit 1
	fi
	shift

	for text in "$@"; do
		sed_escape "$text"
	done
}

process_stdin() {
	if [ $# -gt 1 ]; then
		echo "Too many arguments for -i option." >&2
		usage >&2
		exit 1
	fi

	while IFS= read -r line; do
		sed_escape "$line"
	done
}

main() {
	# Check for inadmissible characters in $extras: / or ].

	case "$extras" in
	*[/]*|*[]]*)
		echo "Invalid characters in extra_chars: / or ]" >&2
		exit 1
		;;
	esac

	# What sort of regular expression are we escaping for?
	if [ "$extended" = 1 ]; then
		meta_chars="$meta_chars$extended_chars"
	fi

	meta_chars="$meta_chars$extras"

	if [ "$stdin" = 1 ]; then
		process_stdin "$@"
	else
		process_arguments "$@"
	fi
}

main "$@"
