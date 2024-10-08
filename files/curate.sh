#!/bin/bash

: ${see:=see}
: ${dirs:=}

exec </dev/tty

for V; do
	if [ ! -e "$V" -o \( ! -n "$dirs" -a -d "$V" \) ]; then continue; fi
	echo
	echo "  >>>>>>  $V"
	echo
	$see "$V"
	done=0
	while [ "$done" = 0 ]; do
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
		IFS= read -r -n1 -p "  ? " C
		echo
		done=0
		case "$C" in
		"h")
			done=1
			;;
		"a")
			$see "$V"
			done=0
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
			V0=$V
			VI=$V
			if [ "$C" = R ]; then
				ext=${V##*.}
				ext=${ext%%\?*}
				V=${V%.*}
				VI=
			fi
			read -p 'rename: ' -e -i "$VI" V1
			if [ -n "$V1" ]; then
				if [ $C = R ]; then
					V1=${V1// /_}.$ext
				fi
				mv -iv -- "$V0" "$V1"
				if [ ! -e "$V0" ]; then
					V=$V1
				fi
			fi
			done=0
			;;
		[0-9])
			mkdir -p ./"$C"
			mv -iv -- "$V" ./"$C"
			done=1
			;;
		m)
			read -p 'move to: ' -e D
			mkdir -p ./"$D"
			mv -iv -- "$V" ./"$D"/
			done=1
			;;
		s)
		        D=`dirname "$V"`
		        mkdir -p "$D/seen"
		        mv -iv -- "$V" "$D/seen"
			done=1
			;;
		*)
			done=0
		esac
	done
	echo
done

