#!/usr/bin/env bash
# [file ...]
# move to rubbish
# suggested: alias rm=move-rubbish
# moves each file to ~/rubbish/${basename}_${timestamp}
# undo with unrubbish

quiet= q=	# move quietly

eval "$(ally)"

verbose=""
if ((!quiet)); then
	verbose="-v -i"
fi

timestamp() {
	date +%Y%m%d_%H%M%S%N%z_%a
}

if [ -z "${RUBBISH:-}" ]; then
	M=$(mount-point "${1:-}")
	if [ "$M" = "$(mount-point "$HOME")" -o "$M" = / ]; then
		RUBBISH="$HOME/.rubbish"
	else
		RUBBISH="$M/.rubbish"
	fi
fi
(umask 0700; mkdir -p "$RUBBISH"; chmod 0700 "$RUBBISH")
status=0
for A; do
	N=$(basename -- "$A")
	while true; do
		B="$RUBBISH/${N}_$(timestamp)_$$"
		[ -e "$B" ] || break  # XXX not entirely secure, should use >| to creat or something?
	done
	mv $verbose -- "$A" "$B" || status=1
	[ -n "${mr_echo:-}" ] && echo "$DEST"
done
exit $status
