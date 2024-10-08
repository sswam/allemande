#!/usr/bin/env bash

# [file or directory]
# Curate files or directories

curate_process_file() {
	local V=$1
	echo
	echo "Where to put $V?"
	echo "  h      - leave here"
	echo "  x      - move to rubbish"
	echo "  X      - remove permanently"
	echo "  r      - rename with initial text & change extension"
	echo "  R      - rename (old)"
	echo "  m      - move to a folder"
	echo "  s      - move to folder 'seen'"
	echo "  a      - see again"
	echo "  0-9    - put in a directory (a single char) - suggest 1-5; 1 means best, 3 average, 5 worst"
	echo "  ^C     - exit"
	IFS= read -r -n1 -p "  ? " C < /dev/tty
	echo
	case "$C" in
		h)
			done=1
			;;
		a)
			"$see" "$V"
			;;
		x)
			move-rubbish "$V"
			done=1
			;;
		X)
			rm -f "$V"
			done=1
			;;
		r|R)
			local V0=$V
			local VI=$V
			if [ "$C" = R ]; then
				local ext=${V##*.}
				ext=${ext%%\?*}
				V=${V%.*}
				VI=
			fi
			read -r -p 'rename: ' -e -i "$VI" V1 </dev/tty
			if [ -n "$V1" ]; then
				if [ "$C" = R ]; then
					V1=${V1// /_}.$ext
				fi
				mv -iv -- "$V0" "$V1"
				if [ ! -e "$V0" ]; then
					V=$V1
				fi
			fi
			;;
		[0-9])
			mkdir -p ./"$C"
			mv -iv -- "$V" ./"$C"
			done=1
			;;
		m)
			read -r -p 'move to: ' -e D </dev/tty
			mkdir -p ./"$D"
			mv -iv -- "$V" ./"$D"/
			done=1
			;;
		s)
			local D
			D=$(dirname "$V")
			mkdir -p "$D/seen"
			mv -iv -- "$V" "$D/seen"
			done=1
			;;
		*)
			;;
	esac
}

curate() {
	local see= s=see	# Command to view files
	local dirs= d=	# Include directories

	eval "$(ally)"

	for V; do
		if [ ! -e "$V" ] || { [ -z "$dirs" ] && [ -d "$V" ]; }; then
			continue
		fi
		echo
		echo "  >>>>>>  $V"
		echo
		"$see" "$V"
		local done=0
		while [ "$done" = 0 ]; do
			curate_process_file "$V"
		done
		echo
	done
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	curate "$@"
fi

# version: 0.1.1
