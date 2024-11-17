# Makefile
# Generates help text for tools listed in tools.txt

SHELL := /bin/bash

.PHONY: all clean

all: tools_help.txt

tools_help.txt: tools.txt
	while read tool; do v "$$tool" --help ; echo; echo; done < $< > $@ 2>&1 | less -F

clean:
	rm -f tools_help.txt

# version: 0.1.0
