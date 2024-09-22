SHELL=bash

all: summary.txt overview.txt

files.txt:
	cd "$$ALLEMANDE_HOME" && git ls-files
log.txt:
	git log --reverse | sed -n '/sam@ucm.dev/,$$p' | grep -v -e '^commit' -e 'Author' -e '^Date' -e '^Merge' | indenter.py --apply t > $@
diary.txt: log.txt
	< $< summary.sh "$$(<task-diary.txt)" > $@
overview.txt: log.txt
	< $< summary.sh "$$(<task-overview.txt)" > $@

structure.txt: files.txt summary.txt

.SECONDARY:
