#!/bin/bash

# llm-loop: run an LLM on all newly modified chat files

# TODO do this in Python

o=              # options
i=2             # interval
v=	        # verbose
b=	        # backup
#b="arcs -N -q"	# backup
q=	        # quiet
r=1	        # reload
m=s             # model
d=              # depth

# o="-d --log llm.log"

. opts

depth=""
if [ -n "$d" ]; then
	depth="-maxdepth $d"
fi

# TODO move functions to separate scripts
# TODO use inotifywait instead of find
# TODO skip updates triggered by llm-loop itself

log() {
	printf "%s: %s\n" "$(date +%F\ %T)" "$*" >&2
}

hr() {
	printf -- "-%.0s" {1..78} >&2
	printf "\n"
}

progname=$(progname "$0")
progpath=$(progpath "$0")

# progmtime=$(stat -c %Y.%N "$progpath")
prog_mtime_human=$(stat -c %y "$progpath")

if [ -n "$v" ]; then v=v; fi
if [ "$b" = 1 ]; then b="arcs"; fi

if [ -z "$q" ]; then
	log "$progname $progmtime"
fi

step=0

while true; do
	$v find . $depth -name '*.chat' -newermt "-$i seconds" | (
		count=0
		while read file; do
			printf "\n\n"
			hr
			log "$file"
			$v $b

			# allow specifying a model name in the filename:

			# with a filename like:  hello@gpt-4.chat
			# the model name is:     gpt-4
			# the base filename is:  hello
			# Can also use abbreviations, i.e. 3+ 4 c i

			base_model=$(basename "$file" .chat)
			base="${base_model%@*}"
			model=$m
			if [ "$base" != "$base_model" ]; then
				model="${base_model#*@}"
			fi

			<"$file" llm chat -m "$model" $o | tee -a "$file" &
			printf "\n"
			count=$[count+1]
		done
		if [ $count -gt 0 ]; then
			log "waiting for $count responses..."
			wait
			$v $b
			$v sleep $[$i + 1]
		else
			$v sleep $[$i - 1]
		fi
	)

#	if [ $[step % 10] -eq 0 ] && [ -z "$q" ]; then
	printf "." >&2
#	fi

	step=$[step+1]

	prog_mtime_human_new=$(stat -c %y "$progpath")

	if [ "$prog_mtime_human_new" != "$prog_mtime_human" ]; then
		echo
		exec "$0" "$@"
	fi
done
