# Makefile

SHELL := /bin/bash
CC=gcc
CFLAGS=-Wall -Wextra -pedantic -std=c99 -ggdb

.PHONY: all clean

exes = pipechat

all: tools_help.txt $(exes)

# Generate help text for tools listed in tools.txt
tools_help.txt: tools.txt
	while read tool; do v "$$tool" --help ; echo; echo; done < $< > $@ 2>&1 | less -F

clean:
	rm -f tools_help.txt

# version: 0.1.0
