LC_ALL=C
SHELL:=bash

dirs.txt: .
	comm -2 -3 <(lsd | grep -vw wip) <(< $@ sort) >> $@.new
	cat $@.new >> $@
	rm $@.new
