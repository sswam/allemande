LC_ALL=C
SHELL:=bash

dirs.txt: .
	comm -2 -3 <(lsd) <(< $@ sort) >> $@.new
	cat $@.new >> $@
	rm $@.new
