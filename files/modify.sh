#!/bin/bash -eu
# [cmd arg ...] : [file ...]
# apply a command to a list of files

p=1	# parallelism
. opts

parallel=$p

CMD=()

n=0
while [ "$1" != : -a $# -gt 0 ]
do
        CMD[$n]=$1
        n=$((n + 1))
        shift
done
if [ "$1" != : ]
then
        echo usage: `basename "$0"` file ... : command >&2
        exit 1
fi
shift

modify1() {
	local F=$1 ; shift
	RUBBISH_NAME=`mr_echo=1 copy-rubbish "$F"` &&
	chmod --reference="$F" "$RUBBISH_NAME" || true
	chown --reference="$F" "$RUBBISH_NAME" || true
	< "$RUBBISH_NAME" "${CMD[@]}" >| "$F"
}

n=0
for F; do
	modify1 "$F" &
	n=$(($n + 1))
	if [ $n -ge $parallel ]
	then
		wait
		n=0
	fi
done
wait

# NOTE: this currently uses my "copy-rubbish" tool
# in order to preserve the same inode and hence hard links.
# It doesn't perform an atomic update, which might also be desirable.
