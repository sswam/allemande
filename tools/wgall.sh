#!/bin/bash
#PARALLEL_MAX=${PARALLEL_MAX:-2}
while read A
do
	B=`basename $A`
	. para wg "$@" "$A"
done
wait
