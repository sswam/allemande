# use this from bash, like:
# PARALLEL_MAX=10
# . parallel command args

# This unfortunately has gotten ugly because I wanted to make it always run
# $PARALLEL_MAX jobs instead of run $PARALLEL_MAX then wait for all to finish,
# then repeat.

lock() {
	local file="$1"
	while true; do
		2>/dev/null mv "$file" "$file.my" && break
		sleep 0.000$RANDOM
	done
}

unlock() {
	local file="$1"
	mv "$file.my" "$file"
}

inc() {
	local file="$1"
	echo >>"$file.my"
}

dec() {
	local A
	local file="$1"
	local size=`wc -l < "$file.my"`
	for A in `seq 1 $[$size-1]`; do
		echo
	done >"$file.my"
}

main() {
	local A

	PARALLEL_MAX="${PARALLEL_MAX:-12}"

	PARALLEL_FILE="/tmp/.parallel.$$"

	if [ ! -e "$PARALLEL_FILE" -a ! -e "$PARALLEL_FILE.my" ]; then
		for A in `seq 1 $PARALLEL_MAX`; do
			echo
		done >"$PARALLEL_FILE"
	fi

	lock "$PARALLEL_FILE"

	while [ ! -s "$PARALLEL_FILE.my" ]; do
		unlock "$PARALLEL_FILE"
		sleep 0.000$RANDOM
		lock "$PARALLEL_FILE"
	done

	(
		"$@"
		lock "$PARALLEL_FILE"
		inc "$PARALLEL_FILE"
		unlock "$PARALLEL_FILE"
	) &

	dec "$PARALLEL_FILE"

	unlock "$PARALLEL_FILE"
}

main "$@"
