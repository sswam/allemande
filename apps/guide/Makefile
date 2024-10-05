# Makefile
# Generates help text for tools listed in tools.txt

SHELL := /bin/bash

.PHONY: all clean

all: tools_help.txt

tools_help.txt: tools.txt
	while read A; do "$$A" --help ; echo; echo; done < $< > $@

clean:
	rm -f tools_help.txt

# version: 0.1.0
