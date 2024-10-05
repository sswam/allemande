#!/usr/bin/make -f

url ?= $(shell search -m 1 -l "site:youtube.com plagueis audiobook playlist" | kut 2)

model=gf

summary_prompt="please summarise the chapter in the same style, tense, person as the orig. dont mention the narrator, author, name of book, ytube, comments, etc., just the story. about 400 words. include '\#\#\# chapter n' headings"

all: summary.md

audio:
	mkdir -p $@
	cd $@ ; \
	youtube-dl-audio --yes-playlist "$(url)"
	touch $@

symlinks: audio
	mkdir -p $@
	cd $@ ; \
	ls -tcr ../$</*.m4a | \
	(i=1; while read file; do ln -s "$$file" `printf %03d $$i`.m4a; i=$$((i+1)); done)
	touch $@

transcripts: symlinks
	mkdir -p $@
	cd $@ ; \
	for file in ../symlinks/*.m4a; do \
		whisp -f txt $$file ; \
	done

summaries: transcripts
	mkdir -p $@
	cd $@ ; \
	for file in ../transcripts/*.txt; do \
		summary=`basename $$file`; \
		[ -e "$$summary" ] || summary -m=$(model) < $$file > $$summary "$(summary_prompt)" $$file ; \
	done

summary.md: summaries
	cat-named -b $</*.txt | squeeze-blank-lines | sed 's/^#File: 0*\([0-9][0-9]*\)\(\.txt\)*/\n## Part \1/' > $@

.SECONDARY:
