progs = ramp-gen ramp-io xramp xramp-aqua ramp
all: $(progs)
ramp-io: main.c colorramp.c gamma-randr.c
	gcc -o $@ $^ -lm -lxcb -lxcb-randr
xramp: xramp.c
	gcc -o $@ $^
devinst: $(progs)
	for prog in $(progs); do \
		ln -sfv $(PWD)/$$prog /usr/local/bin/$$prog; \
	done
