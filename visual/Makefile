all: install chmod

build: everyone.txt girls.txt boys.txt everyone_count.txt girls_count.txt boys_count.txt

everyone.txt: person
	find $< -mindepth 1 -maxdepth 1 -type f -printf "%f\n" | sed 's/\.[^.]*$$//' | shuf >$@

girls.txt: person
	find $< -mindepth 1 -maxdepth 1 -type f | xargs grep -l '^1girl,' | sed 's/\.[^.]*$$//; s,.*/,,;' | shuf >$@

boys.txt: person
	find $< -mindepth 1 -maxdepth 1 -type f | xargs grep -l '^1boy,' | sed 's/\.[^.]*$$//; s,.*/,,;' | shuf >$@

%_count.txt: %.txt
	<$< wc -l >$@

install: build
	ln -sf $$PWD/*.txt $$PWD/person/*.txt ../unprompted/unprompted/templates/

chmod:
	chmod o+rx person/ person/* person/*/*

.PHONY: all build install chmod
