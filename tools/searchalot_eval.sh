#!/bin/bash
# searchalot_eval
for cutoff in `seq 1 10 | tac`; do
	echo "Cutoff $cutoff"
	echo
	echo "Number of items in each list"
	echo
	wc -l *-$cutoff/*-list.txt
	echo
	echo "Number of items in total"
	echo
	cat *-$cutoff/*-list.txt | kutout 1 | uniqo | wc -l
	echo
	echo "Tail of the list"
	echo
	tail *-$cutoff/*-list.txt
	echo
	echo -----------------------------------------------------------------------
	echo 
done | tee eval.txt
