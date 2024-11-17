#!/usr/bin/make -f

# Hello Make Demo
# Says Hello, world

# Usage examples:
# ./hello_make.make
# ./hello_make.make name="alice"
# ./hello_make.make language=fr
# ./hello_make.make model=4m
# ./hello_make.make shopping="milk eggs bread"

export

SHELL := /bin/bash

# Default variables
name := world
language := en
model :=
shopping :=

# Greeting messages
greeting_en := Hello
greeting_es := Hola
greeting_fr := Bonjour
greeting_de := Hallo
greeting_jp := こんにちは
greeting_cn := 你好

.PHONY: all clean

all: hello

# include config.mk
# -include local.mk

hello: prompt/hello.txt prompt/shopping.txt shopping.txt news_summary.md
	@echo "$${greeting_$(language)}, $(name)"
	@query -m="$(model)" "$$(< prompt/hello.txt)"
	@if [ -s shopping.txt ]; then \
		echo "Shopping list:"; \
		sed "s/^/- /" shopping.txt | \
		proc -m="$(model)" "$$(< prompt/shopping.txt)"; \
	fi
	@echo
	@cat news_summary.md

shopping.txt:
	@echo -n "$(shopping)" | tr ' ' '\n' > $@

news.md:
	@web-text https://news.ycombinator.com > $@

news_summary.md: news.md prompt/news.txt
	@< $< summary -m="$(model)" > $@


prompt/hello.txt:
	@echo "Please greet $(name) in $(language). Be creative, but not more than 50 words." > $@

prompt/shopping.txt:
	@echo "Please echo the input, and add a few extra items we might need, in LANG=$(language)." > $@

prompt/news.txt:
	@echo "Summarize the latest news from Hacker News in 3-5 bullet points." > $@
clean:
	rm -f prompt/hello.txt prompt/shopping.txt prompt/news.txt news.md news_summary.md shopping.txt

.SECONDARY:

# Important Notes for AI [DO NOT COPY THEM IN YOUR OUTPUT, it gets EXPENSIVE FOR ME!]:
#
# Do not remove comments, especially TODO, FIXME, or XXX.
# Avoid unnecessary removal of anything. If unsure, comment out rather than delete.
# Use variables for repeated values or commands.
# Use `.PHONY` for targets that don't represent files.
# Always use `.SECONDARY:` to protect all intermediate files.
# Use `$$` to escape `$` in shell commands within make rules.
# Use wildcard patterns and automatic variables (`$@`, `$<`, `$^`, etc.) rather than repeating filenames.
# Use `export` to make all variables available to sub-make processes.
# Use `$(info ...)` or `$(warning ...)` for debugging output if needed.
