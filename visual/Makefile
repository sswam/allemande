dir=$(shell readlink -f .)

all: install chmod

up: sync | all

sync:
	sshc -- $${SERVER_SSH}= sh -c "make install chmod; cd person; git add -A; git commit -m ." || true
	in-dir person git pull

build: everyone.txt girls.txt boys.txt nonbinary.txt people.txt everyone_count.txt girls_count.txt boys_count.txt nonbinary_count.txt people_count.txt

everyone.txt: person
	find $< -mindepth 1 -maxdepth 1 -type f -printf "%f\n" | sed 's/\.[^.]*$$//' | shuf >$@

girls.txt: person
	find $< -mindepth 1 -maxdepth 1 -type f | xa grep -l -w '1girl' | sed 's/\.[^.]*$$//; s,.*/,,;' | shuf >$@

boys.txt: person
	find $< -mindepth 1 -maxdepth 1 -type f | xa grep -l -w '1boy' | sed 's/\.[^.]*$$//; s,.*/,,;' | shuf >$@

nonbinary.txt: person
	find $< -mindepth 1 -maxdepth 1 -type f | xa grep -l -v -w -e '1girl' -e '1boy' | sed 's/\.[^.]*$$//; s,.*/,,;' | shuf >$@

people.txt: girls.txt boys.txt nonbinary.txt
	cat $^ | shuf >$@

%_count.txt: %.txt
	<$< wc -l >$@

install: build
	deadlinks | xa rm
	ln -sf $$PWD/*.txt $$PWD/ar/*.txt $$PWD/person/*/ $$PWD/person/*.txt $$PWD/nsfw/*.txt $$PWD/extra/*.txt $(dir)/../unprompted/unprompted/templates/
	cd $(dir)/../unprompted/unprompted/templates/ ; deadlinks | xa rm

chmod:
	chmod o+rx person/ person/*/ || true
	chmod o+r person/* person/*/* || true

person:
	mkdir -p person

.PHONY: all build install chmod sync sync-all
