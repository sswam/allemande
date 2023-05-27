#!/usr/bin/make -f

SHELL = /bin/bash

default: search-clipped.txt businesses-sorted.txt directories-sorted.txt

mission-raw.txt:
	mike.py -e 800 --pause 1 -n 1 -c 0.6 | tee -a $@
mission-%.txt: mission-raw-%.txt
	gpt process 'Please clean this up and just show the problem statement without any other crap.' <$< | tee $@

queries-%.txt: mission-%.txt
	gpt process "$$(< $(PROG_DIR)/queries.prompt)" <$< | tee $@

landmark-queries.txt: mission-landmarks.txt
	gpt process "$$(< $(PROG_DIR)/queries.prompt)" <$< | tee $@

search.txt: queries.txt
	mkdir -p search
	while read Q; do echo "## $$Q"; echo; QQ=$${Q#[0-9]*. } ; search "$$QQ" | v tee "search/$${Q// /_}.txt"; echo ; echo; done < $< | tee $@

search-clipped.txt: search.txt
	< $< perl -pe 's{https?://}{}; s/\/.*//' | tee $@

businesses.txt: queries.txt mission.txt search.txt
	mkdir -p businesses
	while read Q; do echo "## $$Q"; echo; QQ=$${Q#[0-9]*. } ; F="$${Q// /_}.txt"; cat-sections mission.txt search/$$F | \
		gpt process "$$(< $(PROG_DIR)/businesses.prompt)" | tee "businesses/$$F"; echo ; echo; done < $< | tee $@

directories.txt: queries.txt mission.txt search.txt
	mkdir -p directories
	while read Q; do echo "## $$Q"; echo; QQ=$${Q#[0-9]*. } ; F="$${Q// /_}.txt"; cat-sections mission.txt search/$$F | \
		gpt process "$$(< $(PROG_DIR)/directories.prompt)" | tee "directories/$$F"; echo ; echo; done < $< | tee $@

%-sorted.txt: %.txt
	< $< grep -v '^##' | sed 's/^[^ ]* //' | grep -v '^$' | uniqoc | sort -rn > $@

#directories.txt: mission.txt search-clipped.txt
#	cat-sections $^ | gpt process 'Please make a numbered list of just business directory services and search engines from the search results.' | tee $@
#
#other.txt: mission.txt search-clipped.txt
#	cat-sections $^ | gpt process 'Please make a numbered list of relevant resources which are neither individual businesses nor directory services nor search engines from the search results.' | tee $@
