#!/usr/bin/env bash
# dir
# Prunes files in the specified directories to free up space.

cache-prune() {
	free= f=    # ensure FS free space, e.g. 5G
	reduce= r=  # reduce by this amount, e.g. 50M
	remove= R=  # actually remove files rather than printing them

	eval "$(ally)"

	if [ "$#" != 1 ]; then
		die "Usage: cache-prune [options] [dir]"
	fi

	cache_dir="${1:-.}"

	free=$(space-units-to-kb "$free")
	reduce=$(space-units-to-kb "$reduce")

	if [ "$free" ] && [ "$reduce" ]; then
		die "Cannot use both --free and --reduce options together"
	fi
	if [ -z "$free" ] && [ -z "$reduce" ]; then
		die "Either --free or --reduce option must be specified"
	fi
	if [ "$free" ]; then
		avail=$(df --output=avail "$cache_dir" | tail -n 1)
		reduce=$(( free - avail ))
	fi
	if [ "$reduce" -le 0 ]; then
		exit 0
	fi
	printf >&2 "Pruning cache to free up %s KiB\n" "$reduce"
	prune "$cache_dir" "$reduce" "$remove"
}

space-units-to-kb() {
	local space=$1
	case $space in
		"") echo "";;
		*G|*g) echo $(( ${space%[Gg]} * 1024 * 1024 )) ;;
		*M|*m) echo $(( ${space%[Mm]} * 1024 )) ;;
		*K|*k) echo $(( ${space%[Kk]} )) ;;
		*[0-9]) echo $(( (space + 1023) / 1024 )) ;;
		*) die "Invalid space format: $space" ;;
	esac
}

prune() {
	local dir=$1
	local reduce=$2
	local remove=$3
	find "$dir" -type f | sorttime -t=a -r -s | kut 2 | xa du | sed 's/^ *//; s/ /\t/' |
	(
		total=0
		while IFS=$'\t' read -r size file && [ $total -lt $reduce ]; do
			if [ "$remove" ]; then
				rm -v -f "$file"
			else
				echo "$size	$file"
			fi
			total=$(( total + size ))
		done
	)
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	cache-prune "$@"
fi
