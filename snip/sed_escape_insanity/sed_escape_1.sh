#!/bin/sh
meta_chars='][\.*^$\/\\&'
extended_chars="+?|(){}"
usage() {
	echo "Usage: $0 [-E|--extended] [-x extras] [-i | -- text]"
	echo "Options: -E: Extended regex, -i: Escape stdin, -x: Extra chars, --: Separate options"
}
sed_escape() { printf '%s\n' "$1" | sed "s/[$meta_chars]/\\\\&/g;" | sed ':a;N;$!ba;s/\n/\\n/g'; }
process_arguments() {
	[ $# -eq 0 ] || [ "$1" != "--" ] && {
		usage >&2
		exit 1
	}
	shift
	for text in "$@"; do sed_escape "$text"; done
}
process_stdin() { while IFS= read -r line; do sed_escape "$line"; done; }
main() {
	case "$extras" in *[/]* | *[]]*)
		echo "Invalid chars in extras" >&2
		exit 1
		;;
	esac
	[ "$extended" = 1 ] && meta_chars="$meta_chars$extended_chars"
	meta_chars="$meta_chars$extras"
	[ "$stdin" = 1 ] && process_stdin "$@" || process_arguments "$@"
}
extended=0
stdin=0
while [ $# -gt 0 ]; do
	case "$1" in -E | --extended) extended=1 ;; -i) stdin=1 ;; -x)
		shift
		extras="$1"
		;;
	-h | --help)
		usage
		exit 0
		;;
	--) break ;; -*)
		echo "Unknown option: $1" >&2
		usage >&2
		exit 1
		;;
	*) break ;; esac
	shift
done
main "$@"
