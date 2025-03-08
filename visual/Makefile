all: sync install chmod

person: sync

sync:
	in-dir person git pull

build: everyone.txt girls.txt boys.txt nonbinary.txt people.txt everyone_count.txt girls_count.txt boys_count.txt nonbinary_count.txt people_count.txt

everyone.txt: person
	find $< -mindepth 1 -maxdepth 1 -type f -printf "%f\n" | sed 's/\.[^.]*$$//' | shuf >$@

girls.txt: person
	find $< -mindepth 1 -maxdepth 1 -type f | xa grep -l '^1girl,' | sed 's/\.[^.]*$$//; s,.*/,,;' | shuf >$@

boys.txt: person
	find $< -mindepth 1 -maxdepth 1 -type f | xa grep -l '^1boy,' | sed 's/\.[^.]*$$//; s,.*/,,;' | shuf >$@

nonbinary.txt: person
	find $< -mindepth 1 -maxdepth 1 -type f | xa grep -l '^1person,' | sed 's/\.[^.]*$$//; s,.*/,,;' | shuf >$@

people.txt: girls.txt boys.txt nonbinary.txt
	cat $^ | shuf >$@

%_count.txt: %.txt
	<$< wc -l >$@

install: build
	ln -sf $$PWD/*.txt $$PWD/ar/*.txt $$PWD/person/*/ $$PWD/person/*.txt $$PWD/nsfw/*.txt ../unprompted/unprompted/templates/

chmod:
	chmod o+rx person/ person/*/
	chmod o+r person/* person/*/*

.PHONY: all build install chmod
