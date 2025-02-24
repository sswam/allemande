all: install chmod

build: everyone.txt everyone_count.txt

everyone.txt: person
	find $< -mindepth 1 -maxdepth 1 -type f -printf "%f\n" | sed 's/\.[^.]*$$//' | sort >$@

everyone_count.txt: everyone.txt
	<$< wc -l >$@

install: build
	ln -sf $$PWD/*.txt $$PWD/person/*.txt ../unprompted/unprompted/templates/

chmod:
	chmod o+rx person/ person/* person/*/*

.PHONY: all build install chmod
