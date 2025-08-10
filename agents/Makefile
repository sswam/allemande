LC_ALL=C
SHELL:=bash

dirs.txt: .
	comm -2 -3 <(lsd | grep -vw -e wip -e base -e over) <(< $@ sort) >> $@.new
	cat $@.new >> $@
	rm $@.new
